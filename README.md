# daelimXsoc - AstraSemi Intelligence Hub

Hackathon project about semiconductor industry with AI-powered assistance tools.

## Features

### Module 1: Operations Overview
Analyze shipment logs and factory updates using real-time data interpretation.

### Module 2: Document Interpreter
Simplify complex technician messages and logs into clear, actionable steps.

### Module 3: Image Identifier
AI-powered visual inspection for wafers, parts, and equipment tools.

### Quality Risk Insight Helper
Get beginner-friendly insights about quality observations and process notes. Users can paste a short quality/process observation and receive structured insights with risk levels, key points, and suggested actions.

## Quick Start

### Prerequisites
- Python 3.8+
- OpenAI API Key (optional - app works in mock mode without it)

### Setup Steps

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment**
   Create a `.env` file:
   ```bash
   OPENAI_API_KEY=your_openai_api_key_here
   ```

3. **Run the Application**
   ```bash
   python app.py
   ```

4. **Access the Application**
   - Main Hub: http://localhost:5000
   - Quality Risk Insight Helper: http://localhost:5000/quality-insight

## Quality Risk Insight Helper

### What It Does
The Quality Risk Insight Helper provides beginner-friendly insights about quality observations. It analyzes user-submitted observations and returns:
- Risk level assessment (LOW/MEDIUM/HIGH)
- Simple risk interpretation
- Key points in beginner-friendly language
- Suggested follow-up actions
- Clarifying questions (if needed)
- Mandatory disclaimer

### How to Use (3 Steps)

1. **Enter Your Observation**
   - Type or paste your quality/process observation (20-1000 characters)
   - Use quick-fill chips for common examples
   - Select observation context (optional)

2. **Get Insight**
   - Click "Get Quality Insight" button
   - Wait for AI analysis (usually 2-5 seconds)

3. **Review Results**
   - Check risk level badge
   - Read simple interpretation
   - Review key points and actions
   - Follow suggested next steps

### Example Input
```
Humidity slightly high in Zone C. Minor particle alert earlier. 
No visible defects observed.
```

### Example Output Style
- **Risk Level:** MEDIUM
- **Interpretation:** "The observation shows some environmental variations that may need monitoring. Continue standard procedures."
- **Key Points:**
  - Humidity levels were elevated but within acceptable range
  - Particle alert was minor and resolved quickly
  - No immediate defects detected
- **Actions:**
  - Continue monitoring humidity levels
  - Document the particle alert
  - Report if pattern continues
- **Disclaimer:** "This insight is general guidance and not a technical or engineering assessment."

### Implementation Details

- **Backend:** Flask API endpoint (`POST /api/quality-insight`)
- **LLM:** OpenAI GPT-4o with structured JSON output
- **Validation:** 20-1000 character limit on observations
- **Error Handling:** Graceful fallbacks if LLM unavailable
- **UI:** Minimal, beginner-friendly interface

## API Endpoints

### Quality Insight
- `POST /api/quality-insight` - Generate quality risk insight
  - Request: `{ "observationText": "string", "context": "string" }`
  - Response: `{ "riskLevel": "LOW|MEDIUM|HIGH", "riskInterpretation": "...", "keyPoints": [...], "actions": [...], "clarifyingQuestions": [...], "disclaimer": "..." }`

### Document Interpreter
- `POST /api/interpret` - Simplify technical logs

### Image Identifier
- `POST /api/identify` - Identify semiconductor objects from images

## Project Structure

```
daelimXsoc/
├── app.py                    # Main Flask application
├── quality_insight_api.py    # Quality Insight API endpoint
├── templates/               # HTML templates
│   ├── index.html
│   ├── operations.html
│   ├── interpreter.html
│   ├── identifier.html
│   └── quality_insight.html
├── static/                  # CSS and JS
│   ├── css/
│   └── js/
│       └── quality_insight.js
└── requirements.txt         # Python dependencies
```

## Development

### Testing Quality Risk Insight Helper

**Backend Validation Test:**
```python
# Test that empty observationText is rejected
curl -X POST http://localhost:5000/api/quality-insight \
  -H "Content-Type: application/json" \
  -d '{"observationText": ""}'
# Should return 400 error
```

**Test with Sample Observation:**
```python
curl -X POST http://localhost:5000/api/quality-insight \
  -H "Content-Type: application/json" \
  -d '{"observationText": "Humidity slightly high in Zone C. Minor particle alert earlier.", "context": "Cleanroom environment"}'
```

**Verify Disclaimer:**
All responses must include the disclaimer: "This insight is general guidance and not a technical or engineering assessment."

## License

Hackathon Project - AstraSemi Team
