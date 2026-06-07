import os
import json
import re
from flask import Flask, request, jsonify, send_file
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder='.', static_url_path='')

# Configure Gemini
api_key = os.environ.get("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

SYSTEM_PROMPT = """You are an expert Cyberpunk Cloud Architect.
Your task is to convert a natural language cloud architecture requirement into a structured JSON configuration.
The JSON configuration must strictly match the following JSON Schema:
{
    "title": "Short descriptive architecture title",
    "provider": "AWS Cloud Infrastructure" or other provider name,
    "prompt": "The original user prompt",
    "cost": "$XXX.XX",
    "vulnerabilities": integer (0 to 5),
    "securityScore": integer (0 to 100),
    "costBreakdown": [number for Gateway/CDN, number for Compute Cluster, number for Databases, number for Traffic/Network],
    "nodes": [
        {
            "id": "unique_lowercase_id",
            "type": "network" | "compute" | "database" | "storage",
            "name": "Component Name",
            "spec": "Instance spec or details (e.g. m5.xlarge, Multi-AZ)",
            "ip": "Simulated IP address or access point",
            "icon": "font-awesome 6 icon class (e.g. fa-solid fa-server, fa-solid fa-database, fa-solid fa-cloud, fa-solid fa-globe, fa-solid fa-network-wired)",
            "tier": 1 | 2 | 3,
            "textDim": false or true
        }
    ],
    "connections": [
        {
            "from": "source_node_id",
            "to": "target_node_id",
            "dashed": false or true
        }
    ],
    "recommendations": [
        {
            "title": "Recommendation Title",
            "body": "Detailed description or advice",
            "type": "secure" | "cost" | "warning"
        }
    ],
    "gitMsg": "Git commit message reflecting this architecture change"
}

Important Rules:
1. The output MUST be a single, valid, parseable JSON block.
2. DO NOT wrap the output in any markdown block other than a JSON block, or just return the raw JSON. Do not write any explanations.
3. Ensure that for every connection, the 'from' and 'to' IDs exist in the 'nodes' array.
4. Organize nodes into 'tier' 1, 2, or 3. 1 is typically entry/network/CDN, 2 is compute/worker-nodes, 3 is databases/storages.
5. Try to make the specification highly relevant to the user prompt.
"""

@app.route('/')
def index():
    return send_file('index.html')

@app.route('/api/design', methods=['POST'])
def api_design():
    data = request.json or {}
    user_prompt = data.get('prompt', '').strip()
    
    if not user_prompt:
        return jsonify({"error": "Prompt cannot be empty"}), 400
        
    if not api_key:
        return jsonify({"error": "GEMINI_API_KEY is not configured on the server"}), 500

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(
            f"{SYSTEM_PROMPT}\n\nUser prompt:\n{user_prompt}"
        )
        
        text = response.text.strip()
        # Clean potential markdown wrapping
        json_match = re.search(r'(\{.*\})', text, re.DOTALL)
        if json_match:
            text = json_match.group(1)
            
        parsed_json = json.loads(text)
        return jsonify(parsed_json)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
