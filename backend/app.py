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
    logger.warning("ANTHROPIC_API_KEY not found in environment. Analysis endpoint will fail.")
    client = None
else:
    client = Anthropic(api_key=anthropic_api_key)
    logger.info("Anthropic client initialized successfully")

# System prompt for Claude
SYSTEM_PROMPT = """You are an expert compliance analyst specializing in Qatar Central Bank (QCB) fintech regulations.

Your task is to analyze startup documentation and compare it against QCB regulatory requirements.

You must return ONLY valid JSON in this exact format:
{
  "gaps": [
    {
      "title": "Brief gap title",
      "rule_ref": "QCB regulation reference",
      "evidence": "What the startup currently has (or lacks)",
      "explanation": "Clear explanation of the compliance gap",
      "severity": "high|medium|low"
    }
  ],
  "notes": [
    "Additional observation 1",
    "Additional observation 2"
  ]
}

Severity guidelines:
- HIGH: Critical requirement missing or major non-compliance (e.g., no data residency, no compliance officer)
- MEDIUM: Important requirement partially met or unclear (e.g., AML policy exists but not board-approved)
- LOW: Minor gaps or documentation issues (e.g., missing specific procedures, unclear policies)

Be thorough but fair. If evidence suggests compliance, don't create artificial gaps.
"""


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "claude_configured": client is not None,
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

        # Collect all files
        files_data = []
        for key in request.files:
            file = request.files[key]
            if file.filename:
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
        return jsonify({"error": "File too large. Maximum size is 50MB"}), 413

    except Exception as e:
        logger.error(f"Upload error: {str(e)}", exc_info=True)
        return jsonify({"error": f"Upload failed: {str(e)}"}), 500


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
                "error": "AI analysis not configured. Please set ANTHROPIC_API_KEY environment variable."
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

Analyze the startup's compliance status and identify gaps. Return valid JSON only.
"""

        logger.info(f"Sending prompt to Claude (length: {len(prompt)} chars)")

        # Call Claude API
        try:
            message = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                system=SYSTEM_PROMPT,
                max_tokens=2000,
                temperature=0,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = message.content[0].text
            logger.info(f"Received Claude response (length: {len(response_text)} chars)")

            # Parse JSON response
            try:
                analysis_data = json.loads(response_text)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Claude response as JSON: {e}")
                logger.error(f"Response text: {response_text[:500]}")
                return jsonify({
                    "error": "Failed to parse AI response. Please try again."
                }), 500

            gaps = analysis_data.get("gaps", [])
            notes = analysis_data.get("notes", [])

            # Calculate score and breakdown
            score_breakdown = get_detailed_score_breakdown(gaps)

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
                "gaps": gaps,
                "gap_count": len(gaps),
                "score_breakdown": score_breakdown,
                "recommendations": recommendations,
                "notes": notes,
                "context_chunks_used": len(contexts)
            }

            logger.info(
                f"Analysis complete: Score={response['score']}, "
                f"Gaps={len(gaps)}, Recommendations={len(recommendations)}"
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
