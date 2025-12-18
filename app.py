import os
import pandas as pd
from flask import Flask, render_template, request, jsonify
from openai import OpenAI
from dotenv import load_dotenv
import base64

# 1. Load environment variables from .env
load_dotenv()

app = Flask(__name__)

# 2. Initialize OpenAI Client
# This will try to grab the key, but we handle the error later if it fails
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def is_api_ready():
    """Helper to check if the API key is present and looks valid."""
    key = os.getenv("OPENAI_API_KEY")
    return key is not None and key.startswith("sk-")

# --- NAVIGATION ROUTES ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/interpreter')
def interpreter_page():
    return render_template('interpreter.html')

@app.route('/identifier')
def identifier_page():
    # Placeholder for Module 3
    return render_template('identifier.html')

# --- MODULE 1: OPERATIONS LOGIC ---

@app.route('/operations', methods=['GET', 'POST'])
def operations():
    shipments = []
    analysis = None
    
    if request.method == 'POST':
        file = request.files.get('csv_file')
        if file and file.filename.endswith('.csv'):
            try:
                # Read the CSV
                df = pd.read_csv(file)
                shipments = df.to_dict(orient='records')
                
                if is_api_ready():
                    # LIVE API CALL
                    csv_context = df.head(10).to_string()
                    prompt = f"Analyze this data:\n{csv_context}\nProvide: 1. Main Points, 2. Anomalies, 3. Top 3 Priorities."
                    
                    response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": "You are an AstraSemi Ops Expert."},
                            {"role": "user", "content": prompt}
                        ]
                    )
                    analysis = response.choices[0].message.content
                else:
                    # FALLBACK TO MOCK
                    analysis = "### [MOCK MODE] Analysis\n- **Main:** 10 shipments found.\n- **Unusual:** SHP002 is flagged 'Delayed'.\n- **Top 3:** 1. Update logs, 2. Contact carrier, 3. Verify stock."
            
            except Exception as e:
                # Catch Authentication or Data errors
                analysis = f"⚠️ **System Note:** Could not reach AI. Please check your API key or CSV format. (Error: {str(e)})"
    
    return render_template('operations.html', shipments=shipments, analysis=analysis)

# --- MODULE 2: INTERPRETER LOGIC ---

@app.route('/api/interpret', methods=['POST'])
def api_interpret():
    data = request.json
    user_text = data.get("text", "")
    mode = data.get("mode", "summary")
    
    prompts = {
        "summary": "Simplify this AstraSemi log for a trainee. Use beginner-friendly language.",
        "email": "Convert this log into a professional email for a department head.",
        "manager": "Summarize this for a manager's daily update focusing on impact."
    }
    
    if is_api_ready():
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": prompts.get(mode)},
                    {"role": "user", "content": user_text}
                ]
            )
            return jsonify({"analysis": response.choices[0].message.content})
        except Exception as e:
            return jsonify({"analysis": f"⚠️ Authentication Error: {str(e)}"})
    
    return jsonify({"analysis": f"**[MOCK {mode.upper()}]**\nEverything looks operational. Proceed with standard protocol."})

# MODULE 3: Image Identifier (Wafer/Tool Vision)

def encode_image(image_file):
    return base64.b64encode(image_file.read()).decode('utf-8')

# --- MODULE 3: VISION LOGIC ---

@app.route('/api/identify', methods=['POST'])
def api_identify():
    if 'image' not in request.files:
        return jsonify({"analysis": "No image uploaded."}), 400
    
    image_file = request.files['image']
    base64_image = encode_image(image_file)

    if is_api_ready():
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Identify this semiconductor object for a new trainee. Explain what it is, its usage, and its role in the process. Use simple language."},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                            },
                        ],
                    }
                ],
                max_tokens=300,
            )
            return jsonify({"analysis": response.choices[0].message.content})
        except Exception as e:
            return jsonify({"analysis": f"⚠️ Vision API Error: {str(e)}"})
    
    # Mock Response
    return jsonify({"analysis": "**[MOCK VISION]**\n\n**Object:** Silicon Wafer\n**Usage:** The base substrate for microchips.\n**Role:** It acts as the 'canvas' where circuits are printed using light."})

if __name__ == '__main__':
    app.run(debug=True)
