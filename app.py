from flask import Flask, request, jsonify, render_template_string
from datetime import datetime, timedelta
import uuid
import os

app = Flask(__name__)

# --- Backend: Data Storage & Logic ---
# Using a list to store dictionaries (In-memory)
registry_data = []

def compute_health_status(last_date_str, days_limit):
    """Logic to track 'Last Service Date' vs. 'Current Date'"""
    last_date = datetime.strptime(last_date_str, "%Y-%m-%d")
    expiry_date = last_date + timedelta(days=int(days_limit))
    
    if datetime.now() > expiry_date:
        return "URGENT", "red"
    return "STABLE", "green"

# --- API: CRUD Functionality ---

@app.route('/api/units', methods=['GET'])
def get_all_units():
    processed_list = []
    for unit in registry_data:
        status_label, color = compute_health_status(unit['last_service'], unit['interval'])
        unit_copy = unit.copy()
        unit_copy['status'] = status_label
        unit_copy['color'] = color
        processed_list.append(unit_copy)
    return jsonify(processed_list)

@app.route('/api/units', methods=['POST'])
def add_unit():
    payload = request.json
    new_entry = {
        "id": str(uuid.uuid4())[:8],
        "name": payload.get('name'),
        "job": payload.get('job'),
        "last_service": payload.get('last_service'),
        "interval": payload.get('interval')
    }
    registry_data.append(new_entry)
    return jsonify({"message": "Machine added"}), 201

@app.route('/api/units/<id>', methods=['DELETE'])
def remove_unit(id):
    global registry_data
    registry_data = [u for u in registry_data if u['id'] != id]
    return jsonify({"message": "Machine removed"})

# --- Frontend: HTML/JavaScript ---

INDEX_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Maintenance Tracker</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #f4f7f6; padding: 40px; }
        .container { max-width: 600px; margin: auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        .unit-card { border-left: 5px solid; padding: 10px; margin: 10px 0; display: flex; justify-content: space-between; align-items: center; background: #fafafa; }
        .red { border-color: #e74c3c; color: #e74c3c; }
        .green { border-color: #2ecc71; color: #2ecc71; }
        input { width: 90%; padding: 8px; margin: 5px 0; border: 1px solid #ddd; border-radius: 4px; }
        button { background: #3498db; color: white; border: none; padding: 10px 15px; cursor: pointer; border-radius: 4px; }
        .del-btn { background: #95a5a6; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <h2>🛠 Machine Maintenance Logger</h2>
        <div id="form">
            <input type="text" id="name" placeholder="Machine Name (e.g. Generator)">
            <input type="text" id="job" placeholder="Task (e.g. Oil Change)">
            <input type="date" id="date">
            <input type="number" id="interval" placeholder="Interval Days (e.g. 50)">
            <button onclick="saveMachine()">Add Machine</button>
        </div>
        <hr>
        <div id="displayArea"></div>
    </div>

    <script>
        async function loadMachines() {
            const res = await fetch('/api/units');
            const data = await res.json();
            const area = document.getElementById('displayArea');
            area.innerHTML = data.map(m => `
                <div class="unit-card ${m.color}">
                    <div>
                        <strong>${m.name}</strong> - ${m.job}<br>
                        <small>Status: ${m.status} (Last: ${m.last_service})</small>
                    </div>
                    <button class="del-btn" onclick="deleteMachine('${m.id}')">Delete</button>
                </div>
            `).join('');
        }

        async function saveMachine() {
            const payload = {
                name: document.getElementById('name').value,
                job: document.getElementById('job').value,
                last_service: document.getElementById('date').value,
                interval: document.getElementById('interval').value
            };
            await fetch('/api/units', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(payload)
            });
            loadMachines();
        }

        async function deleteMachine(id) {
            await fetch(`/api/units/${id}`, { method: 'DELETE' });
            loadMachines();
        }

        loadMachines();
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(INDEX_HTML)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
