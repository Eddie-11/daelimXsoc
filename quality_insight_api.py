"""
API endpoint for Quality Risk Insight Helper
"""
from flask import Blueprint, request, jsonify
from openai import OpenAI
import os
import json
import re
import logging

logger = logging.getLogger(__name__)

quality_bp = Blueprint('quality', __name__, url_prefix='/api')

# Initialize OpenAI Client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def is_api_ready():
    """Check if OpenAI API key is available"""
    key = os.getenv("OPENAI_API_KEY")
    return key is not None and key.startswith("sk-")


def parse_json_response(text):
    """Extract JSON from LLM response, handling markdown code blocks"""
    # Try to find JSON in code blocks
    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except:
            pass
    
    # Try to find JSON object directly
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except:
            pass
    
    return None


def generate_quality_insight(observation_text: str, context: str = "General process note") -> dict:
    """
    Generate quality insight using LLM
    Returns structured response with risk level, interpretation, and actions
    """
    system_prompt = """You are a helpful quality assistant for semiconductor manufacturing. 
Your role is to provide beginner-friendly insights about quality observations.

IMPORTANT RULES:
- Be beginner-friendly and use simple language
- Do NOT provide technical diagnosis or defect prediction
- Use words like "may", "might", "could" - never claim certainty
- Provide practical, actionable next steps
- Keep responses short and scannable
- Always include the exact disclaimer: "This insight is general guidance and not a technical or engineering assessment."

Output ONLY valid JSON matching this exact structure:
{
  "riskLevel": "LOW|MEDIUM|HIGH",
  "riskInterpretation": "1-2 sentences explaining the observation in simple terms",
  "keyPoints": ["bullet point 1", "bullet point 2", "bullet point 3"],
  "actions": ["action 1", "action 2", "action 3"],
  "clarifyingQuestions": ["question 1", "question 2"] or [],
  "disclaimer": "This insight is general guidance and not a technical or engineering assessment."
}"""

    user_prompt = f"""Context: {context}

Observation: {observation_text}

Task: Analyze this observation and provide a structured quality insight. 
Return ONLY the JSON object with no additional text."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        response_text = response.choices[0].message.content
        parsed = parse_json_response(response_text)
        
        if parsed:
            # Validate required fields
            if 'disclaimer' not in parsed:
                parsed['disclaimer'] = "This insight is general guidance and not a technical or engineering assessment."
            if 'riskLevel' not in parsed:
                parsed['riskLevel'] = 'MEDIUM'
            if 'riskInterpretation' not in parsed:
                parsed['riskInterpretation'] = "The observation requires attention and follow-up."
            if 'keyPoints' not in parsed:
                parsed['keyPoints'] = ["Review the observation details", "Consult with supervisor if needed"]
            if 'actions' not in parsed:
                parsed['actions'] = ["Document the observation", "Follow standard procedures", "Report if necessary"]
            if 'clarifyingQuestions' not in parsed:
                parsed['clarifyingQuestions'] = []
            
            return parsed
        else:
            # Fallback response
            logger.warning("Failed to parse LLM response, using fallback")
            return {
                "riskLevel": "MEDIUM",
                "riskInterpretation": "The observation has been noted and requires standard follow-up procedures.",
                "keyPoints": [
                    "Document the observation clearly",
                    "Follow standard operating procedures",
                    "Report to supervisor if needed"
                ],
                "actions": [
                    "Review observation details",
                    "Check standard procedures",
                    "Consult with team if uncertain"
                ],
                "clarifyingQuestions": [
                    "When did this observation occur?",
                    "Has this been observed before?"
                ],
                "disclaimer": "This insight is general guidance and not a technical or engineering assessment."
            }
            
    except Exception as e:
        logger.error(f"Error calling LLM: {e}")
        raise


@quality_bp.route('/quality-insight', methods=['POST'])
def quality_insight():
    """POST /api/quality-insight - Generate quality risk insight"""
    try:
        data = request.json
        
        # Validation
        observation_text = data.get('observationText', '').strip()
        context = data.get('context', 'General process note').strip()
        
        if not observation_text:
            return jsonify({'error': 'observationText is required'}), 400
        
        if len(observation_text) < 20:
            return jsonify({'error': 'observationText must be at least 20 characters'}), 400
        
        if len(observation_text) > 1000:
            return jsonify({'error': 'observationText must be at most 1000 characters'}), 400
        
        # Generate insight
        if is_api_ready():
            try:
                result = generate_quality_insight(observation_text, context)
                return jsonify(result), 200
            except Exception as e:
                logger.error(f"Error generating insight: {e}")
                # Return safe fallback
                return jsonify({
                    "riskLevel": "MEDIUM",
                    "riskInterpretation": "Unable to process observation at this time. Please consult with your supervisor.",
                    "keyPoints": [
                        "Document the observation",
                        "Follow standard procedures",
                        "Report to supervisor"
                    ],
                    "actions": [
                        "Review standard operating procedures",
                        "Consult with team members",
                        "Escalate if needed"
                    ],
                    "clarifyingQuestions": [],
                    "disclaimer": "This insight is general guidance and not a technical or engineering assessment."
                }), 200
        else:
            # Mock response when API not available
            return jsonify({
                "riskLevel": "LOW",
                "riskInterpretation": "The observation appears routine. Continue monitoring and follow standard procedures.",
                "keyPoints": [
                    "Observation has been noted",
                    "No immediate action required",
                    "Continue standard monitoring"
                ],
                "actions": [
                    "Document the observation",
                    "Continue normal operations",
                    "Report any changes"
                ],
                "clarifyingQuestions": [
                    "Is this a recurring observation?",
                    "Are there any patterns to note?"
                ],
                "disclaimer": "This insight is general guidance and not a technical or engineering assessment."
            }), 200
            
    except Exception as e:
        logger.error(f"Error in quality_insight endpoint: {e}")
        return jsonify({'error': 'Internal server error'}), 500

