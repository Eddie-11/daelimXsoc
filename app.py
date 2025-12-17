import os
import io
import base64
import pandas as pd
from flask import Flask, render_template, request, jsonify
from openai import OpenAI
from dotenv import load_dotenv
from werkzeug.utils import secure_filename

# --- CONFIGURATION ---
load_dotenv()
app = Flask(__name__)
app.secret_key = "astrasemi_secret_key"
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Use a temporary folder for image uploads
UPLOAD_FOLDER = 'data/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def is_api_ready():
    return os.getenv("OPENAI_API_KEY") is not None

# --- HELPER FUNCTIONS ---

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

# --- ROUTES ---

@app.route('/')
def index():
    return render_template('index.html')

# MODULE 1: Operations Overview (CSV Upload & Summary)
@app.route('/operations', methods=['GET', 'POST'])
def operations():
    shipments = []
    analysis = None
    
    if request.method == 'POST':
        file = request.files.get('csv_file')
        if file and file.filename.endswith('.csv'):
            df = pd.read_csv(file)
            shipments = df.to_dict(orient='records')
            
            # Prepare context for AI
            csv_sample = df.head(10).to_string()
            prompt = f"Analyze this semiconductor shipment data:\n{csv_sample}\nProvide: 1. Main Points, 2. Unusual findings/Anomalies, 3. Top 3 Priorities for a new employee."

            if is_api_ready():
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "system", "content": "You are an AstraSemi Ops Expert."},
                              {"role": "user", "content": prompt}]
                )
                analysis = response.choices[0].message.content
            else:
                analysis = "### MOCK ANALYSIS\n- **Main:** 10 active shipments.\n- **Unusual:** SHP002 is delayed.\n- **Top 3:** 1. Check Austin log, 2. Confirm yield, 3. Update status."

    return render_template('operations.html', shipments=shipments, analysis=analysis)

# MODULE 2: Document Interpreter (Text Snippets)
@app.route('/api/interpret', methods=['POST'])
def interpret():
    user_text = request.json.get("text", "")
    
    if is_api_ready():
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": "Simplify this semiconductor log for a trainee. Use simple words and highlight risks."},
                      {"role": "user", "content": user_text}]
        )
        return jsonify({"analysis": response.choices[0].message.content})
    
    return jsonify({"analysis": f"MOCK: '{user_text}' interpreted as 'Normal operating procedure. No risks detected.'" })

# MODULE 3: Image Identifier (Wafer/Tool Vision)
@app.route('/api/identify', methods=['POST'])
def identify():
    file = request.files.get('image')
    if not file:
        return jsonify({"error": "No image"}), 400
    
    filepath = os.path.join(UPLOAD_FOLDER, secure_filename(file.filename))
    file.save(filepath)
    
    if is_api_ready():
        base64_img = encode_image(filepath)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": "Identify this semiconductor part or wafer. List any visible defects or important features for a new employee."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_img}"}}
                ]
            }]
        )
        return jsonify({"analysis": response.choices[0].message.content})

    return jsonify({"analysis": "MOCK: Image identified as a 'Silicon Wafer (Type-P)'. Surface looks clear."})

if __name__ == '__main__':
    app.run(debug=True)