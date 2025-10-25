"""
Flask backend API for Fintech Regulatory Readiness Platform.
Provides endpoints for document upload, analysis, and recommendations.
"""

import os
import json
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from anthropic import Anthropic, APIError
from werkzeug.exceptions import RequestEntityTooLarge

from rag import build_index, search, get_index_stats, clear_index
from rules import load_rules, get_rules_text, get_rules_summary
from scoring import compute_score, get_detailed_score_breakdown
from recommender import recommend, get_all_programs, get_all_experts, search_resources

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# Initialize Anthropic client
anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
if not anthropic_api_key:
    logger.warning("ANTHROPIC_API_KEY not found in environment. Analysis endpoint will be disabled.")
    client = None
else:
    client = Anthropic(api_key=anthropic_api_key)
    logger.info("Anthropic client initialized successfully")

# System prompt for Claude
SYSTEM_PROMPT = """You are a helpful compliance analyst evaluating Qatar Central Bank (QCB) fintech licensing readiness.

CRITICAL PARADIGM SHIFT: Focus on STRENGTHS first, gaps second. A well-prepared startup should score 65-85/100.

YOUR TASK:
1. Identify what the startup HAS DONE WELL (strengths)
2. Identify what needs improvement (gaps)

SCORING APPROACH:
- Strengths ADD points (most startups should have 5-8 strengths)
- Gaps SUBTRACT points (most startups should have 2-4 gaps)
- Well-prepared startup: 5-8 strengths, 2-4 minor gaps = 65-85 points

CRITICAL: Return ONLY valid JSON. NO markdown code blocks. Start with { and end with }.

Required format:
{
  "strengths": [
    {
      "title": "Brief strength title",
      "rule_ref": "QCB regulation reference",
      "evidence": "What the startup has done well",
      "explanation": "Why this demonstrates good readiness",
      "quality": "excellent|good|adequate"
    }
  ],
  "gaps": [
    {
      "title": "Brief gap title",
      "rule_ref": "QCB regulation reference",
      "evidence": "What the startup currently lacks",
      "explanation": "Clear explanation of the gap",
      "severity": "high|medium|low"
    }
  ],
  "notes": [
    "Overall positive observations"
  ]
}

STRENGTH QUALITY LEVELS:
- "excellent": Comprehensive, well-documented, exceeds basic requirements (+15 points)
- "good": Well-documented, meets requirements with minor room for enhancement (+12 points)
- "adequate": Documented, meets minimum requirements (+10 points)

GAP SEVERITY LEVELS:
- "high": Critical requirement completely missing (-15 points)
- "medium": Important element needs development (-10 points)
- "low": Minor improvement needed (-5 points)

WHAT TO IDENTIFY AS STRENGTHS:
✓ Business plan exists and is comprehensive
✓ AML/CFT policy documented (even if pending board approval)
✓ Compliance officer identified
✓ Capital commitment demonstrated
✓ Cybersecurity framework documented
✓ Corporate governance structure outlined
✓ CDD procedures documented
✓ Source of funds verification procedures in place

ONLY flag as gaps if TRULY missing or severely inadequate. Be generous - reward what they have!
"""


def extract_json_from_response(text: str) -> str:
    """
    Extract JSON from Claude's response, handling markdown code blocks if present.

    Args:
        text: Raw response text from Claude

    Returns:
        Cleaned JSON string
    """
    text = text.strip()

    # Check if wrapped in markdown code block
    if text.startswith("```json"):
        # Remove ```json from start and ``` from end
        text = text[7:]  # Remove ```json
        if text.endswith("```"):
            text = text[:-3]  # Remove ```
        text = text.strip()
    elif text.startswith("```"):
        # Generic code block
        text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

    return text


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "claude_configured": client is not None,
        "api_key_present": anthropic_api_key is not None,
        "index_stats": get_index_stats()
    })


@app.route('/upload', methods=['POST'])
def upload_files():
    """
    Upload and index documents.

    Accepts multipart/form-data with one or more files.
    Returns indexing statistics.
    """
    try:
        logger.info("Received upload request")

        # Check if files were provided
        if not request.files:
            return jsonify({"error": "No files provided"}), 400

        # Collect all files (handle multiple files with same key 'files')
        files_data = []
        uploaded_files = request.files.getlist('files')

        if not uploaded_files:
            # Fallback: try iterating through all keys
            for key in request.files:
                uploaded_files.extend(request.files.getlist(key))

        for file in uploaded_files:
            if file and file.filename:
                file_bytes = file.read()
                files_data.append((file_bytes, file.filename))
                logger.info(f"Received file: {file.filename} ({len(file_bytes)} bytes)")

        if not files_data:
            return jsonify({"error": "No valid files found"}), 400

        # Build index
        try:
            stats = build_index(files_data)
            logger.info(f"Index built: {stats}")

            return jsonify({
                "success": True,
                "message": f"Successfully indexed {stats['files_processed']} files",
                **stats
            })

        except ValueError as e:
            logger.error(f"Indexing error: {str(e)}")
            return jsonify({"error": str(e)}), 400

    except RequestEntityTooLarge:
        return jsonify({
            "error": "File too large. Maximum size is 50MB per file.",
            "code": "FILE_TOO_LARGE",
            "max_size_mb": 50
        }), 413

    except Exception as e:
        logger.error(f"Upload error: {str(e)}", exc_info=True)
        return jsonify({
            "error": f"Upload failed: {str(e)}",
            "code": "UPLOAD_ERROR"
        }), 500


@app.route('/analyze', methods=['POST'])
def analyze_compliance():
    """
    Analyze startup compliance against QCB regulations.

    Expects JSON body with:
    {
      "summary": "Startup description and key facts"
    }

    Returns compliance analysis with gaps, score, and recommendations.
    """
    try:
        logger.info("Received analysis request")

        # Check if Claude is configured
        if client is None:
            return jsonify({
                "error": "AI analysis not configured. Please set ANTHROPIC_API_KEY environment variable.",
                "requires_api_key": True,
                "code": "MISSING_API_KEY"
            }), 503

        # Check if index exists
        stats = get_index_stats()
        if not stats["indexed"]:
            return jsonify({
                "error": "No documents have been uploaded yet. Please upload documents first."
            }), 400

        # Parse request
        data = request.get_json()
        if not data or not data.get("summary"):
            return jsonify({"error": "Missing 'summary' in request body"}), 400

        startup_summary = data["summary"]
        logger.info(f"Analyzing startup with summary: {startup_summary[:100]}...")

        # Retrieve relevant document chunks
        search_results = search(startup_summary, k=10)
        contexts = [chunk for _, chunk, _ in search_results]
        context_text = "\n\n---\n\n".join(contexts)

        # Get QCB rules
        rules_text = get_rules_text()

        # Construct prompt
        prompt = f"""
STARTUP DOCUMENTATION EXCERPTS:
{context_text}

STARTUP DECLARED SUMMARY:
{startup_summary}

QCB REGULATORY REQUIREMENTS:
{rules_text}

TASK: Evaluate this startup's readiness to apply for QCB licensing. Be GENEROUS - they have documentation and understanding. Only flag 2-4 real gaps that genuinely need attention. A well-prepared startup should score 65-85 points.

CRITICAL: Return ONLY raw JSON starting with {{ and ending with }}. NO markdown, NO code blocks, NO extra text.
"""

        logger.info(f"Sending prompt to Claude (length: {len(prompt)} chars)")

        # Call Claude API
        try:
            message = client.messages.create(
                model="claude-sonnet-4-5-20250929",
                system=SYSTEM_PROMPT,
                max_tokens=4000,
                temperature=0,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = message.content[0].text
            logger.info(f"Received Claude response (length: {len(response_text)} chars)")

            # Extract and parse JSON response
            try:
                # Clean the response (remove markdown code blocks if present)
                cleaned_json = extract_json_from_response(response_text)
                logger.info(f"Cleaned JSON (first 200 chars): {cleaned_json[:200]}")

                analysis_data = json.loads(cleaned_json)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Claude response as JSON: {e}")
                logger.error(f"Original response: {response_text[:1000]}")
                logger.error(f"Cleaned response: {cleaned_json[:1000] if 'cleaned_json' in locals() else 'N/A'}")
                return jsonify({
                    "error": "Failed to parse AI response. The AI returned invalid JSON format. Please try again.",
                    "debug_info": response_text[:500] if logger.level == logging.DEBUG else None
                }), 500

            strengths = analysis_data.get("strengths", [])
            gaps = analysis_data.get("gaps", [])
            notes = analysis_data.get("notes", [])

            # Calculate score and breakdown (NEW: pass strengths AND gaps)
            score_breakdown = get_detailed_score_breakdown(strengths, gaps)

            # Generate recommendations
            recommendations = recommend(gaps)

            # Prepare response
            response = {
                "success": True,
                "score": score_breakdown["final_score"],
                "grade": score_breakdown["grade"],
                "category": score_breakdown["category"],
                "color": score_breakdown["color"],
                "needs_expert_review": score_breakdown["needs_expert_review"],
                "strengths": strengths,
                "strength_count": len(strengths),
                "gaps": gaps,
                "gap_count": len(gaps),
                "score_breakdown": score_breakdown,
                "recommendations": recommendations,
                "notes": notes,
                "context_chunks_used": len(contexts)
            }

            logger.info(
                f"Analysis complete: Score={response['score']}, "
                f"Strengths={len(strengths)}, Gaps={len(gaps)}, "
                f"Recommendations={len(recommendations)}"
            )

            return jsonify(response)

        except APIError as e:
            logger.error(f"Anthropic API error: {str(e)}")
            return jsonify({
                "error": f"AI service error: {str(e)}"
            }), 503

    except Exception as e:
        logger.error(f"Analysis error: {str(e)}", exc_info=True)
        return jsonify({"error": f"Analysis failed: {str(e)}"}), 500


@app.route('/rules', methods=['GET'])
def get_rules():
    """Get all QCB regulatory rules."""
    try:
        rules = load_rules()
        summary = get_rules_summary()
        return jsonify({
            "rules": rules,
            "summary": summary
        })
    except Exception as e:
        logger.error(f"Error loading rules: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/resources', methods=['GET'])
def get_resources():
    """Get all QDB programs and compliance experts."""
    try:
        programs = get_all_programs()
        experts = get_all_experts()
        return jsonify({
            "programs": programs,
            "experts": experts,
            "total_programs": len(programs),
            "total_experts": len(experts)
        })
    except Exception as e:
        logger.error(f"Error loading resources: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/resources/search', methods=['POST'])
def search_resources_endpoint():
    """Search programs and experts by keyword."""
    try:
        data = request.get_json()
        query = data.get("query", "")

        if not query:
            return jsonify({"error": "Missing 'query' parameter"}), 400

        results = search_resources(query)
        return jsonify(results)

    except Exception as e:
        logger.error(f"Error searching resources: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/clear', methods=['POST'])
def clear_data():
    """Clear indexed documents."""
    try:
        clear_index()
        return jsonify({
            "success": True,
            "message": "Index cleared successfully"
        })
    except Exception as e:
        logger.error(f"Error clearing index: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/demo', methods=['GET'])
def demo_analysis():
    """
    Return a sample analysis for demonstration purposes.
    Shows users what the output looks like without requiring uploads or AI analysis.
    """
    try:
        # Sample STRENGTHS - what the startup has done well
        sample_strengths = [
            {
                "title": "Comprehensive AML/CFT Policy Framework",
                "rule_ref": "QCB 1.1.4",
                "evidence": "Detailed AML/CFT policy covering transaction monitoring, suspicious activity reporting, and customer screening procedures",
                "explanation": "Your AML/CFT framework is thorough and demonstrates strong understanding of regulatory requirements. It includes specific thresholds, escalation procedures, and clear roles and responsibilities.",
                "quality": "good"
            },
            {
                "title": "Strong Business Plan with Market Analysis",
                "rule_ref": "General Requirements",
                "evidence": "Comprehensive business plan with financial projections, market analysis, and clear value proposition",
                "explanation": "Your business plan is detailed and shows clear understanding of Qatar's fintech market. Financial projections are realistic and well-supported.",
                "quality": "excellent"
            },
            {
                "title": "Cybersecurity Framework Documented",
                "rule_ref": "QCB 2.3.1",
                "evidence": "ISO 27001-aligned cybersecurity framework with incident response procedures and security controls",
                "explanation": "Your cybersecurity approach follows industry best practices and demonstrates excellent preparation for QCB security requirements with comprehensive controls.",
                "quality": "excellent"
            },
            {
                "title": "Capital Adequacy Commitment",
                "rule_ref": "QCB 3.1.1",
                "evidence": "Committed capital of QAR 10,000,000 with shareholder agreements in place",
                "explanation": "Capital requirements are clearly understood and commitments are documented through shareholder agreements.",
                "quality": "good"
            },
            {
                "title": "Corporate Governance Structure Defined",
                "rule_ref": "QCB 4.1.1",
                "evidence": "Board of 3 directors identified including independent members, with governance framework outlined",
                "explanation": "Your governance structure meets QCB requirements with appropriate board composition and clear reporting lines.",
                "quality": "adequate"
            },
            {
                "title": "Customer Due Diligence Procedures",
                "rule_ref": "QCB 1.2.1",
                "evidence": "Enhanced CDD procedures documented covering identity verification and beneficial ownership",
                "explanation": "Your CDD procedures are well-documented and cover the key requirements for customer onboarding and monitoring.",
                "quality": "good"
            }
        ]

        # Sample gaps - only 2 minor issues
        sample_gaps = [
            {
                "title": "Data Residency Implementation Timeline",
                "rule_ref": "QCB 2.1.1",
                "evidence": "Plan to use Qatar-based data centers documented but specific timeline and provider not confirmed",
                "explanation": "While you've identified the data residency requirement, provide a specific timeline and confirm Qatar-based hosting arrangements.",
                "severity": "medium"
            },
            {
                "title": "Business Continuity Testing Schedule",
                "rule_ref": "QCB Operational Risk",
                "evidence": "Business continuity plan exists but annual testing schedule not specified",
                "explanation": "Include a specific schedule for annual BCP testing and document the testing procedures.",
                "severity": "low"
            }
        ]

        # Calculate score (NEW: pass strengths AND gaps)
        score_breakdown = get_detailed_score_breakdown(sample_strengths, sample_gaps)

        # Get recommendations
        recommendations = recommend(sample_gaps)

        # Sample notes
        sample_notes = [
            "Your business plan demonstrates strong market understanding and clear value proposition for Qatar's fintech ecosystem",
            "Core compliance framework is well-established with comprehensive AML and cybersecurity policies in place",
            "Documentation is thorough and shows clear understanding of QCB regulatory requirements",
            "The identified gaps are primarily procedural and can be addressed within 2-3 weeks",
            "Capital adequacy and operational infrastructure meet QCB standards for payment processing services",
            "Strong foundation for licensing application - recommend scheduling pre-application meeting with QCB"
        ]

        response = {
            "success": True,
            "score": score_breakdown["final_score"],
            "grade": score_breakdown["grade"],
            "category": score_breakdown["category"],
            "color": score_breakdown["color"],
            "needs_expert_review": score_breakdown["needs_expert_review"],
            "strengths": sample_strengths,
            "strength_count": len(sample_strengths),
            "gaps": sample_gaps,
            "gap_count": len(sample_gaps),
            "score_breakdown": score_breakdown,
            "recommendations": recommendations,
            "notes": sample_notes,
            "context_chunks_used": 15,
            "is_demo": True  # Flag to indicate this is sample data
        }

        logger.info("Returning demo analysis results")
        return jsonify(response)

    except Exception as e:
        logger.error(f"Demo endpoint error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"Internal error: {str(error)}")
    return jsonify({"error": "Internal server error"}), 500


if __name__ == '__main__':
    # Load rules and resources on startup to check for errors
    try:
        rules = load_rules()
        logger.info(f"Loaded {len(rules)} rules on startup")
    except Exception as e:
        logger.error(f"Failed to load rules: {e}")

    try:
        programs = get_all_programs()
        experts = get_all_experts()
        logger.info(f"Loaded {len(programs)} programs and {len(experts)} experts on startup")
    except Exception as e:
        logger.error(f"Failed to load resources: {e}")

    # Run app
    port = int(os.getenv("PORT", 5000))
    logger.info(f"Starting Flask server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=os.getenv("FLASK_DEBUG", "False") == "True")
