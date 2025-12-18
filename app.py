import os
import pandas as pd
from flask import Flask, render_template, request, jsonify
from openai import OpenAI
from dotenv import load_dotenv
import markdown as md
import base64
import numpy as np
from datetime import datetime, timedelta
import json

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

@app.route('/predictive', methods=['GET', 'POST'])
def predictive_page():
    # Module 4: Predictive Analysis for Equipment Aging
    return render_template('predictive.html')

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
                    # Convert markdown to HTML for safe rendering in the template
                    try:
                        analysis_html = md.markdown(analysis, extensions=["extra", "nl2br"])
                    except Exception:
                        analysis_html = analysis.replace("\n", "<br>")
                else:
                    # FALLBACK TO MOCK
                    analysis = "### [MOCK MODE] Analysis\n- **Main:** 10 shipments found.\n- **Unusual:** SHP002 is flagged 'Delayed'.\n- **Top 3:** 1. Update logs, 2. Contact carrier, 3. Verify stock."
                    analysis_html = md.markdown(analysis, extensions=["extra", "nl2br"])

            except Exception as e:
                # Catch Authentication or Data errors
                analysis = f"⚠️ **System Note:** Could not reach AI. Please check your API key or CSV format. (Error: {str(e)})"
                analysis_html = md.markdown(analysis)

    # Ensure analysis_html is defined when template expects it
    if analysis is None:
        analysis_html = None
    return render_template('operations.html', shipments=shipments, analysis=analysis, analysis_html=analysis_html)

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
            analysis = response.choices[0].message.content
            # Convert markdown to HTML for proper rendering
            try:
                analysis_html = md.markdown(analysis, extensions=["extra", "nl2br"])
            except Exception:
                analysis_html = analysis.replace("\n", "<br>")
            return jsonify({"analysis": analysis, "analysis_html": analysis_html})
        except Exception as e:
            error_text = f"⚠️ Vision API Error: {str(e)}"
            error_html = md.markdown(error_text)
            return jsonify({"analysis": error_text, "analysis_html": error_html})

    # Mock Response
    mock_analysis = "**[MOCK VISION]**\n\n**Object:** Silicon Wafer\n**Usage:** The base substrate for microchips.\n**Role:** It acts as the 'canvas' where circuits are printed using light."
    mock_html = md.markdown(mock_analysis, extensions=["extra", "nl2br"])
    return jsonify({"analysis": mock_analysis, "analysis_html": mock_html})

# --- MODULE 4: PREDICTIVE ANALYSIS LOGIC ---

def process_equipment_data(df):
    """Process equipment data from CSV DataFrame"""
    processed_data = []

    for _, row in df.iterrows():
        # Extract data from CSV row
        machine_id = row.get('Machine ID', f"MCH{str(len(processed_data) + 1).zfill(3)}")
        runtime_hours = float(row.get('Runtime Hours', 0))
        last_maintenance_days = float(row.get('Last Maintenance Days', 0))
        temperature = float(row.get('Temperature', 70))
        vibration = float(row.get('Vibration', 5.0))
        error_codes_str = str(row.get('Error Codes', '')).strip()

        # Parse error codes (split by comma if multiple)
        error_codes = [code.strip() for code in error_codes_str.split(',') if code.strip()]
        error_count = len(error_codes)

        # Calculate failure probability using the same algorithm as before
        runtime_risk = min(1.0, runtime_hours / 10000)
        temp_risk = max(0, (temperature - 80) / 40)  # Risk increases above 80°C
        vibration_risk = max(0, (vibration - 8) / 12)  # Risk increases above 8
        maintenance_risk = min(1.0, last_maintenance_days / 365)  # Risk increases over time

        failure_probability = min(0.95, runtime_risk * 0.3 + temp_risk * 0.25 +
                                 vibration_risk * 0.25 + maintenance_risk * 0.2)

        # Health score (0-100, inverse of failure probability)
        health_score = max(5, 100 - (failure_probability * 95))

        # Recommended maintenance date
        if failure_probability > 0.7:
            days_to_maintenance = np.random.uniform(1, 7)
        elif failure_probability > 0.5:
            days_to_maintenance = np.random.uniform(7, 30)
        elif failure_probability > 0.3:
            days_to_maintenance = np.random.uniform(30, 90)
        else:
            days_to_maintenance = np.random.uniform(90, 180)

        maintenance_date = datetime.now() + timedelta(days=int(days_to_maintenance))

        processed_data.append({
            'machine_id': machine_id,
            'runtime_hours': round(runtime_hours, 1),
            'last_maintenance_days': round(last_maintenance_days, 0),
            'temperature': round(temperature, 1),
            'vibration': round(vibration, 2),
            'error_codes': error_codes,
            'error_count': error_count,
            'failure_probability': round(failure_probability, 3),
            'health_score': round(health_score, 1),
            'recommended_maintenance': maintenance_date.strftime('%Y-%m-%d'),
            'days_to_maintenance': int(days_to_maintenance)
        })

    return processed_data

def generate_equipment_analysis(equipment_data):
    """Generate AI analysis for equipment data"""
    if not equipment_data:
        return "No equipment data available for analysis."

    # Calculate summary statistics
    high_risk_count = sum(1 for item in equipment_data if item['failure_probability'] > 0.7)
    avg_health = np.mean([item['health_score'] for item in equipment_data])
    critical_machines = [item for item in equipment_data if item['failure_probability'] > 0.7][:5]

    # Create AI prompt
    critical_info = ""
    if critical_machines:
        critical_info = "\n\n**Critical Machines Requiring Immediate Attention:**\n"
        for machine in critical_machines:
            critical_info += f"- {machine['machine_id']}: Health Score {machine['health_score']}, {machine['days_to_maintenance']} days to maintenance\n"

    prompt = f"""
    Analyze this semiconductor equipment dataset for predictive maintenance:

    **Summary:**
    - Total Machines: {len(equipment_data)}
    - High Risk Machines: {high_risk_count}
    - Average Health Score: {avg_health:.1f}/100
    {critical_info}

    Provide a comprehensive analysis covering:
    1. Overall Equipment Health Assessment
    2. Critical Maintenance Priorities
    3. Risk Mitigation Strategies
    4. Operational Recommendations
    5. Resource Planning Suggestions

    Focus on actionable insights for maintenance scheduling and risk reduction.
    """

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a semiconductor equipment reliability expert. Provide detailed, actionable maintenance recommendations based on equipment data analysis."},
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content

def generate_equipment_data(num_machines=20):
    """Generate simulated equipment data"""
    np.random.seed(42)  # For consistent data generation
    machine_ids = [f"MCH{str(i+1).zfill(3)}" for i in range(num_machines)]

    data = []
    for machine_id in machine_ids:
        # Base runtime hours (1000-10000 hours)
        runtime_hours = np.random.uniform(1000, 10000)

        # Last maintenance (0-365 days ago)
        days_since_maintenance = np.random.uniform(0, 365)

        # Temperature (正常运营温度 around 70°C, with variation)
        temperature = np.random.normal(70, 15)
        temperature = max(40, min(120, temperature))  # Clamp between 40-120°C

        # Vibration (normal around 5.0, increases with runtime)
        base_vibration = 5.0
        runtime_factor = runtime_hours / 10000
        vibration = base_vibration + runtime_factor * np.random.uniform(0, 10)
        vibration = max(1.0, min(20, vibration))

        # Error codes (0-5, more with higher runtime/vibration)
        error_count = max(0, int((runtime_hours / 2000 + vibration / 5) * np.random.uniform(0, 3)))
        error_codes = [f"E{str(np.random.randint(100, 999)).zfill(3)}" for _ in range(error_count)]

        # Calculate failure probability based on factors
        runtime_risk = runtime_hours / 10000
        temp_risk = max(0, (temperature - 80) / 40)  # Risk increases above 80°C
        vibration_risk = max(0, (vibration - 8) / 12)  # Risk increases above 8
        maintenance_risk = days_since_maintenance / 365  # Risk increases over time

        failure_probability = min(0.95, runtime_risk * 0.3 + temp_risk * 0.25 +
                                 vibration_risk * 0.25 + maintenance_risk * 0.2)

        # Health score (0-100, inverse of failure probability)
        health_score = max(5, 100 - (failure_probability * 95))

        # Recommended maintenance date
        if failure_probability > 0.7:
            days_to_maintenance = np.random.uniform(1, 7)
        elif failure_probability > 0.5:
            days_to_maintenance = np.random.uniform(7, 30)
        elif failure_probability > 0.3:
            days_to_maintenance = np.random.uniform(30, 90)
        else:
            days_to_maintenance = np.random.uniform(90, 180)

        maintenance_date = datetime.now() + timedelta(days=int(days_to_maintenance))

        data.append({
            'machine_id': machine_id,
            'runtime_hours': round(runtime_hours, 1),
            'last_maintenance_days': round(days_since_maintenance, 0),
            'temperature': round(temperature, 1),
            'vibration': round(vibration, 2),
            'error_codes': error_codes,
            'error_count': len(error_codes),
            'failure_probability': round(failure_probability, 3),
            'health_score': round(health_score, 1),
            'recommended_maintenance': maintenance_date.strftime('%Y-%m-%d'),
            'days_to_maintenance': int(days_to_maintenance)
        })

    return data

@app.route('/api/predictive-data', methods=['GET', 'POST'])
def api_predictive_data():
    """API endpoint to get predictive analysis data"""
    try:
        equipment_data = []

        if request.method == 'POST':
            # Process uploaded CSV file
            if 'csv_file' not in request.files:
                return jsonify({"error": "No CSV file uploaded"}), 400

            file = request.files['csv_file']
            if file.filename == '':
                return jsonify({"error": "No file selected"}), 400

            if not file.filename.endswith('.csv'):
                return jsonify({"error": "File must be a CSV file"}), 400

            # Process uploaded CSV file with robust parsing
            try:
                # Read CSV with robust parsing for error codes
                file_content = file.read().decode('utf-8')
                lines = file_content.split('\n')

                if not lines:
                    return jsonify({"error": "Empty CSV file"}), 400

                # Parse header
                header = lines[0].strip().split(',')
                data_rows = []

                for line in lines[1:]:
                    if not line.strip():
                        continue
                    # Split first 5 columns, then join the rest as error codes
                    parts = line.strip().split(',', 5)  # Split into max 6 parts
                    if len(parts) < 5:
                        continue

                    # Pad missing values to ensure we have exactly 6 columns
                    while len(parts) < 6:
                        parts.append('')

                    data_rows.append(parts)

                # Create DataFrame
                df = pd.DataFrame(data_rows, columns=header)

                # Process the equipment data
                equipment_data = process_equipment_data(df)

                if not equipment_data:
                    return jsonify({"error": "No valid equipment data found in CSV"}), 400

                print(f"Loaded {len(equipment_data)} machines from uploaded CSV: {file.filename}")

            except Exception as e:
                return jsonify({"error": f"Failed to process CSV file: {str(e)}"}), 500

        else:
            # Load equipment data from existing CSV files (default behavior)
            csv_files = [
                'equipment_data_fab_a.csv',
                'equipment_data_fab_b.csv',
                'equipment_data_aging.csv',
                'equipment_data_new.csv',
                'equipment_data_critical.csv'
            ]

            for csv_file in csv_files:
                try:
                    # Read CSV with robust parsing for error codes
                    with open(csv_file, 'r') as f:
                        lines = f.read().split('\n')

                    if not lines:
                        continue

                    # Parse header
                    header = lines[0].strip().split(',')
                    data_rows = []

                    for line in lines[1:]:
                        if not line.strip():
                            continue
                        # Split first 5 columns, then join the rest as error codes
                        parts = line.strip().split(',', 5)  # Split into max 6 parts
                        if len(parts) < 5:
                            continue

                        # Pad missing values to ensure we have exactly 6 columns
                        while len(parts) < 6:
                            parts.append('')

                        data_rows.append(parts)

                    # Create DataFrame
                    df = pd.DataFrame(data_rows, columns=header)

                    # Process the equipment data
                    file_equipment_data = process_equipment_data(df)
                    equipment_data.extend(file_equipment_data)

                except FileNotFoundError:
                    print(f"Warning: CSV file {csv_file} not found")
                except Exception as e:
                    print(f"Error processing {csv_file}: {e}")
                    continue

            if not equipment_data:
                # Fallback to generated data if no CSV files found
                equipment_data = generate_equipment_data()
                print("Using generated data as fallback")

            print(f"Loaded {len(equipment_data)} machines from default CSV files")

        # Calculate summary statistics
        high_risk_count = sum(1 for item in equipment_data if item['failure_probability'] > 0.7)
        avg_health = np.mean([item['health_score'] for item in equipment_data])

        # Simulate trend data for charts
        trend_data = []
        for i in range(12):  # Last 12 months
            month = datetime.now() - timedelta(days=30*i)
            avg_failure_prob = np.random.uniform(0.2, 0.6)  # Simulated historical data
            trend_data.append({
                'month': month.strftime('%Y-%m'),
                'avg_failure_probability': round(avg_failure_prob, 3),
                'incidents': np.random.randint(0, 5)
            })

        trend_data.reverse()  # Show oldest to newest

        response_data = {
            'equipment': equipment_data,
            'summary': {
                'total_machines': len(equipment_data),
                'high_risk_count': high_risk_count,
                'average_health_score': round(avg_health, 1),
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            },
            'trends': trend_data
        }

        return jsonify(response_data)

    except Exception as e:
        return jsonify({"error": f"Failed to load predictive data: {str(e)}"}), 500

@app.route('/api/predictive-analysis', methods=['POST'])
def api_predictive_analysis():
    """AI-powered predictive analysis endpoint"""
    data = request.json
    machine_id = data.get('machine_id', '')

    if is_api_ready():
        try:
            # Find machine data
            equipment_data = generate_equipment_data()
            machine_data = next((m for m in equipment_data if m['machine_id'] == machine_id), None)

            if not machine_data:
                return jsonify({"error": "Machine not found"}), 404

            # Create AI analysis prompt
            prompt = f"""
            Analyze this semiconductor equipment for predictive maintenance:

            Machine: {machine_data['machine_id']}
            Runtime: {machine_data['runtime_hours']} hours
            Temperature: {machine_data['temperature']}°C
            Vibration: {machine_data['vibration']}
            Error Count: {machine_data['error_count']}
            Health Score: {machine_data['health_score']}/100
            Failure Probability: {machine_data['failure_probability']*100:.1f}%
            Days to Maintenance: {machine_data['days_to_maintenance']}

            Provide a detailed analysis covering:
            1. Risk Assessment
            2. Maintenance Recommendations
            3. Operational Impact
            4. Preventive Actions
            """

            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a semiconductor equipment reliability expert. Provide concise, actionable maintenance recommendations."},
                    {"role": "user", "content": prompt}
                ]
            )

            analysis = response.choices[0].message.content
            analysis_html = md.markdown(analysis, extensions=["extra", "nl2br"])

            return jsonify({
                "analysis": analysis,
                "analysis_html": analysis_html,
                "machine_data": machine_data
            })

        except Exception as e:
            error_text = f"⚠️ Analysis Error: {str(e)}"
            error_html = md.markdown(error_text)
            return jsonify({"analysis": error_text, "analysis_html": error_html})

    # Mock AI Analysis
    mock_analysis = f"""### Predictive Analysis for {machine_id}

**Risk Assessment:** {'🔴 HIGH RISK' if machine_data.get('failure_probability', 0) > 0.7 else '🟡 MODERATE RISK' if machine_data.get('failure_probability', 0) > 0.4 else '🟢 LOW RISK'}

**Key Findings:**
- **Health Score:** {machine_data.get('health_score', 0)}/100
- **Failure Risk:** {machine_data.get('failure_probability', 0)*100:.1f}%
- **Critical Factors:** {'High temperature and vibration detected' if machine_data.get('temperature', 0) > 85 else 'Normal operating conditions'}

**Maintenance Recommendations:**
- Schedule maintenance within {machine_data.get('days_to_maintenance', 30)} days
- Monitor temperature sensors closely
- Check vibration dampening systems

**Operational Impact:**
- Risk of unplanned downtime: {machine_data.get('failure_probability', 0)*100:.0f}%
- Potential production loss: {'HIGH' if machine_data.get('failure_probability', 0) > 0.7 else 'MODERATE'}
"""

    mock_html = md.markdown(mock_analysis, extensions=["extra", "nl2br"])
    return jsonify({
        "analysis": mock_analysis,
        "analysis_html": mock_html,
        "machine_data": data
    })

if __name__ == '__main__':
    app.run(debug=True)
