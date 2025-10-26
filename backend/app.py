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

from rag import build_index, search, get_index_stats, clear_index, get_documents
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
3. FOR EACH FINDING: Cite the specific document and extract an exact quote

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
      "quality": "excellent|good|adequate",
      "document_name": "exact_filename.docx",
      "text_snippet": "Exact quote from document showing this strength (50-150 chars)"
    }
  ],
  "gaps": [
    {
      "title": "Brief gap title",
      "rule_ref": "QCB regulation reference",
      "evidence": "What the startup currently lacks",
      "explanation": "Clear explanation of the gap",
      "severity": "high|medium|low",
      "document_name": "exact_filename.docx where gap was identified, or 'General' if not document-specific",
      "text_snippet": "Exact quote from document showing the issue (50-150 chars), or empty string if General"
    }
  ],
  "notes": [
    "Overall positive observations"
  ]
}

CRITICAL CITATION REQUIREMENTS:
1. ALWAYS provide "document_name" - use the EXACT filename from [Document: filename.docx] tags in the context
2. ALWAYS provide "text_snippet" - copy a SHORT exact quote (50-150 chars) from the document that supports your finding
3. The text_snippet MUST be an EXACT substring from the document (word-for-word match)
4. Choose snippets that clearly show the strength or gap
5. For strengths: pick text showing what they DID
6. For gaps: pick text showing what's MISSING or INADEQUATE
7. If a finding is based on absence of information across all docs, use document_name: "General"

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

EXAMPLE of good citations:
{
  "title": "Strong AML Policy",
  "document_name": "compliance_policy.docx",
  "text_snippet": "We implement enhanced due diligence for all high-risk customers including PEP screening"
}
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

        # Retrieve relevant document chunks with metadata
        search_results = search(startup_summary, k=10)

        # Format contexts with document source information
        formatted_contexts = []
        for score, chunk, metadata in search_results:
            filename = metadata.get("filename", "unknown")
            formatted_contexts.append(f"[Document: {filename}]\n{chunk}")
        context_text = "\n\n---\n\n".join(formatted_contexts)

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

            # Log document citations for debugging
            logger.info(f"Strengths with citations: {len([s for s in strengths if s.get('document_name')])}/{len(strengths)}")
            logger.info(f"Gaps with citations: {len([g for g in gaps if g.get('document_name')])}/{len(gaps)}")

            # Calculate score and breakdown (NEW: pass strengths AND gaps)
            score_breakdown = get_detailed_score_breakdown(strengths, gaps)

            # Generate recommendations
            recommendations = recommend(gaps)

            # Helper function to find text snippet in document with fuzzy matching
            def find_snippet_in_text(full_text: str, snippet: str) -> int:
                """
                Find snippet in text with multiple strategies:
                1. Exact match
                2. Case-insensitive match
                3. Normalized whitespace match
                4. Fuzzy match (first 30 chars)
                """
                if not snippet:
                    return -1

                # Strategy 1: Exact match
                idx = full_text.find(snippet)
                if idx != -1:
                    return idx

                # Strategy 2: Case-insensitive match
                idx = full_text.lower().find(snippet.lower())
                if idx != -1:
                    return idx

                # Strategy 3: Normalized whitespace
                normalized_text = " ".join(full_text.split())
                normalized_snippet = " ".join(snippet.split())
                idx = normalized_text.find(normalized_snippet)
                if idx != -1:
                    # Find approximate position in original text
                    return full_text.find(normalized_snippet.split()[0])

                # Strategy 4: Fuzzy match on first 30 characters
                if len(snippet) > 30:
                    short_snippet = snippet[:30]
                    idx = full_text.lower().find(short_snippet.lower())
                    if idx != -1:
                        return idx

                return -1

            # Build document annotations
            documents = get_documents()
            document_annotations = []

            logger.info(f"Building annotations for {len(documents)} documents")

            for doc in documents:
                doc_annotations = {
                    "filename": doc["filename"],
                    "full_text": doc["full_text"],
                    "annotations": []
                }

                # Find all strengths and gaps that reference this document
                for strength in strengths:
                    if strength.get("document_name") == doc["filename"]:
                        text_snippet = strength.get("text_snippet", "")
                        # Try to find the snippet in the document with fuzzy matching
                        start_idx = find_snippet_in_text(doc["full_text"], text_snippet)

                        if start_idx == -1 and text_snippet:
                            logger.warning(f"Could not find snippet in {doc['filename']}: '{text_snippet[:50]}...'")
                        else:
                            logger.info(f"Matched strength snippet in {doc['filename']} at position {start_idx}")

                        doc_annotations["annotations"].append({
                            "type": "strength",
                            "title": strength["title"],
                            "explanation": strength["explanation"],
                            "quality": strength["quality"],
                            "rule_ref": strength.get("rule_ref", ""),
                            "text_snippet": text_snippet,
                            "start_index": start_idx if start_idx != -1 else None,
                            "end_index": start_idx + len(text_snippet) if start_idx != -1 else None
                        })

                for gap in gaps:
                    if gap.get("document_name") == doc["filename"]:
                        text_snippet = gap.get("text_snippet", "")
                        start_idx = find_snippet_in_text(doc["full_text"], text_snippet)

                        if start_idx == -1 and text_snippet:
                            logger.warning(f"Could not find gap snippet in {doc['filename']}: '{text_snippet[:50]}...'")
                        else:
                            logger.info(f"Matched gap snippet in {doc['filename']} at position {start_idx}")

                        doc_annotations["annotations"].append({
                            "type": "gap",
                            "title": gap["title"],
                            "explanation": gap["explanation"],
                            "severity": gap["severity"],
                            "rule_ref": gap.get("rule_ref", ""),
                            "text_snippet": text_snippet,
                            "start_index": start_idx if start_idx != -1 else None,
                            "end_index": start_idx + len(text_snippet) if start_idx != -1 else None
                        })

                document_annotations.append(doc_annotations)

            # Log annotation summary
            total_annotations = sum(len(doc["annotations"]) for doc in document_annotations)
            logger.info(f"Created {total_annotations} annotations across {len(document_annotations)} documents")
            for doc in document_annotations:
                logger.info(f"  {doc['filename']}: {len(doc['annotations'])} annotations")

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
                "context_chunks_used": len(formatted_contexts),
                "documents": document_annotations  # NEW: Document-level annotations
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
                "quality": "good",
                "document_name": "aml_policy.docx",
                "text_snippet": "AML/CFT framework covers transaction monitoring, suspicious activity reporting, and customer screening procedures"
            },
            {
                "title": "Strong Business Plan with Market Analysis",
                "rule_ref": "General Requirements",
                "evidence": "Comprehensive business plan with financial projections, market analysis, and clear value proposition",
                "explanation": "Your business plan is detailed and shows clear understanding of Qatar's fintech market. Financial projections are realistic and well-supported.",
                "quality": "excellent",
                "document_name": "business_plan.docx",
                "text_snippet": "Qatar's digital payment market is expanding rapidly with increasing smartphone penetration"
            },
            {
                "title": "Cybersecurity Framework Documented",
                "rule_ref": "QCB 2.3.1",
                "evidence": "ISO 27001-aligned cybersecurity framework with incident response procedures and security controls",
                "explanation": "Your cybersecurity approach follows industry best practices and demonstrates excellent preparation for QCB security requirements with comprehensive controls.",
                "quality": "excellent",
                "document_name": "cybersecurity_framework.docx",
                "text_snippet": "cybersecurity approach follows industry best practices and demonstrates excellent preparation for QCB security requirements"
            },
            {
                "title": "Capital Adequacy Commitment",
                "rule_ref": "QCB 3.1.1",
                "evidence": "Committed capital of QAR 10,000,000 with shareholder agreements in place",
                "explanation": "Capital requirements are clearly understood and commitments are documented through shareholder agreements.",
                "quality": "good",
                "document_name": "business_plan.docx",
                "text_snippet": "committed capital of QAR 10,000,000 with shareholder agreements in place"
            },
            {
                "title": "Corporate Governance Structure Defined",
                "rule_ref": "QCB 4.1.1",
                "evidence": "Board of 3 directors identified including independent members, with governance framework outlined",
                "explanation": "Your governance structure meets QCB requirements with appropriate board composition and clear reporting lines.",
                "quality": "adequate",
                "document_name": "business_plan.docx",
                "text_snippet": "Board of 3 directors including independent members, with governance framework outlined"
            },
            {
                "title": "Customer Due Diligence Procedures",
                "rule_ref": "QCB 1.2.1",
                "evidence": "Enhanced CDD procedures documented covering identity verification and beneficial ownership",
                "explanation": "Your CDD procedures are well-documented and cover the key requirements for customer onboarding and monitoring.",
                "quality": "good",
                "document_name": "aml_policy.docx",
                "text_snippet": "Enhanced CDD procedures documented covering identity verification and beneficial ownership"
            }
        ]

        # Sample gaps - only 2 minor issues
        sample_gaps = [
            {
                "title": "Data Residency Implementation Timeline",
                "rule_ref": "QCB 2.1.1",
                "evidence": "Plan to use Qatar-based data centers documented but specific timeline and provider not confirmed",
                "explanation": "While you've identified the data residency requirement, provide a specific timeline and confirm Qatar-based hosting arrangements.",
                "severity": "medium",
                "document_name": "business_plan.docx",
                "text_snippet": "plan to use Qatar-based data centers documented but specific timeline and provider not confirmed"
            },
            {
                "title": "Business Continuity Testing Schedule",
                "rule_ref": "QCB Operational Risk",
                "evidence": "Business continuity plan exists but annual testing schedule not specified",
                "explanation": "Include a specific schedule for annual BCP testing and document the testing procedures.",
                "severity": "low",
                "document_name": "business_plan.docx",
                "text_snippet": "Business Continuity Plan exists but annual testing schedule not specified"
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

        # Sample documents with annotations
        sample_documents = [
            {
                "filename": "business_plan.docx",
                "full_text": "FinPay Qatar Business Plan\n\nExecutive Summary\n\nFinPay is a digital payment processing platform designed for Qatar's growing fintech ecosystem. Our company follows comprehensive KYC procedures for all customers, including identity verification and address confirmation. We have assembled a Board of 3 directors including independent members, with governance framework outlined in our Corporate Governance Policy.\n\nFinancial Projections\n\nWe have committed capital of QAR 10,000,000 with shareholder agreements in place. Our three-year financial projections show sustainable growth with clear revenue models from transaction fees and merchant services.\n\nMarket Analysis\n\nQatar's digital payment market is expanding rapidly with increasing smartphone penetration and government support for financial innovation. Our value proposition focuses on seamless integration with local banking systems while maintaining world-class security standards.\n\nOperational Infrastructure\n\nWe plan to use Qatar-based data centers documented but specific timeline and provider not confirmed. Our Business Continuity Plan exists but annual testing schedule not specified in current documentation.",
                "annotations": [
                    {
                        "type": "strength",
                        "title": "Strong Business Plan with Market Analysis",
                        "explanation": "Your business plan is detailed and shows clear understanding of Qatar's fintech market. Financial projections are realistic and well-supported.",
                        "quality": "excellent",
                        "rule_ref": "General Requirements",
                        "text_snippet": "Qatar's digital payment market is expanding rapidly with increasing smartphone penetration",
                        "start_index": 580,
                        "end_index": 668
                    },
                    {
                        "type": "strength",
                        "title": "Capital Adequacy Commitment",
                        "explanation": "Capital requirements are clearly understood and commitments are documented through shareholder agreements.",
                        "quality": "good",
                        "rule_ref": "QCB 3.1.1",
                        "text_snippet": "committed capital of QAR 10,000,000 with shareholder agreements in place",
                        "start_index": 492,
                        "end_index": 565
                    },
                    {
                        "type": "strength",
                        "title": "Corporate Governance Structure Defined",
                        "explanation": "Your governance structure meets QCB requirements with appropriate board composition and clear reporting lines.",
                        "quality": "adequate",
                        "rule_ref": "QCB 4.1.1",
                        "text_snippet": "Board of 3 directors including independent members, with governance framework outlined",
                        "start_index": 280,
                        "end_index": 366
                    },
                    {
                        "type": "gap",
                        "title": "Data Residency Implementation Timeline",
                        "explanation": "While you've identified the data residency requirement, provide a specific timeline and confirm Qatar-based hosting arrangements.",
                        "severity": "medium",
                        "rule_ref": "QCB 2.1.1",
                        "text_snippet": "plan to use Qatar-based data centers documented but specific timeline and provider not confirmed",
                        "start_index": 829,
                        "end_index": 926
                    },
                    {
                        "type": "gap",
                        "title": "Business Continuity Testing Schedule",
                        "explanation": "Include a specific schedule for annual BCP testing and document the testing procedures.",
                        "severity": "low",
                        "rule_ref": "QCB Operational Risk",
                        "text_snippet": "Business Continuity Plan exists but annual testing schedule not specified",
                        "start_index": 932,
                        "end_index": 1006
                    }
                ]
            },
            {
                "filename": "aml_policy.docx",
                "full_text": "FinPay AML/CFT Policy Document\n\nVersion 1.2 - Last Updated: January 2025\n\n1. Introduction\n\nThis Anti-Money Laundering and Countering the Financing of Terrorism (AML/CFT) policy establishes FinPay's framework for preventing financial crime.\n\n2. Customer Due Diligence\n\nWe implement Enhanced CDD procedures documented covering identity verification and beneficial ownership for all customers. Our process includes:\n\n- Identity document verification (QID/Passport)\n- Address verification through utility bills\n- Beneficial ownership identification for corporate accounts\n- PEP (Politically Exposed Persons) screening\n- Ongoing monitoring and periodic review\n\n3. Transaction Monitoring\n\nOur AML/CFT framework covers transaction monitoring, suspicious activity reporting, and customer screening procedures. We have established specific thresholds of QAR 55,000 for enhanced due diligence and automated alerts for unusual patterns.\n\n4. Suspicious Activity Reporting\n\nClear escalation procedures are defined with designated AML Compliance Officer responsible for STR submissions to Qatar Financial Information Unit (QFIU). All staff receive annual AML training.\n\n5. Record Keeping\n\nAll customer records and transaction data are retained for minimum 10 years in accordance with QCB requirements.",
                "annotations": [
                    {
                        "type": "strength",
                        "title": "Comprehensive AML/CFT Policy Framework",
                        "explanation": "Your AML/CFT framework is thorough and demonstrates strong understanding of regulatory requirements. It includes specific thresholds, escalation procedures, and clear roles and responsibilities.",
                        "quality": "good",
                        "rule_ref": "QCB 1.1.4",
                        "text_snippet": "AML/CFT framework covers transaction monitoring, suspicious activity reporting, and customer screening procedures",
                        "start_index": 652,
                        "end_index": 762
                    },
                    {
                        "type": "strength",
                        "title": "Customer Due Diligence Procedures",
                        "explanation": "Your CDD procedures are well-documented and cover the key requirements for customer onboarding and monitoring.",
                        "quality": "good",
                        "rule_ref": "QCB 1.2.1",
                        "text_snippet": "Enhanced CDD procedures documented covering identity verification and beneficial ownership",
                        "start_index": 285,
                        "end_index": 374
                    }
                ]
            },
            {
                "filename": "cybersecurity_framework.docx",
                "full_text": "FinPay Cybersecurity Framework\n\nISO 27001 Alignment\n\nOur cybersecurity approach follows industry best practices and demonstrates excellent preparation for QCB security requirements with comprehensive controls aligned to ISO 27001:2013 standards.\n\n1. Security Controls\n\n- Access Management: Role-based access control (RBAC)\n- Encryption: AES-256 for data at rest, TLS 1.3 for data in transit\n- Network Security: Firewall rules, intrusion detection/prevention systems\n- Vulnerability Management: Quarterly penetration testing\n- Security Monitoring: 24/7 SOC with SIEM integration\n\n2. Incident Response\n\nComprehensive incident response procedures documented including:\n- Incident classification matrix\n- Escalation workflows\n- Communication protocols\n- Post-incident review process\n\n3. Business Continuity\n\nDisaster recovery procedures with RTO of 4 hours and RPO of 1 hour. Backup systems tested quarterly.\n\n4. Compliance\n\nRegular security audits and compliance assessments conducted by external certified auditors. Last audit completed December 2024 with no critical findings.",
                "annotations": [
                    {
                        "type": "strength",
                        "title": "Cybersecurity Framework Documented",
                        "explanation": "Your cybersecurity approach follows industry best practices and demonstrates excellent preparation for QCB security requirements with comprehensive controls.",
                        "quality": "excellent",
                        "rule_ref": "QCB 2.3.1",
                        "text_snippet": "cybersecurity approach follows industry best practices and demonstrates excellent preparation for QCB security requirements",
                        "start_index": 59,
                        "end_index": 180
                    }
                ]
            }
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
            "is_demo": True,  # Flag to indicate this is sample data
            "documents": sample_documents  # NEW: Sample document annotations
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
