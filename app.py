"""
pojia-breaker Web UI — Flask app for Railway deployment
Warm paper aesthetic, full attack orchestration interface
"""
import os
import sys
import json
import subprocess
from pathlib import Path
from flask import Flask, render_template, request, jsonify, Response
import yaml

app = Flask(__name__)

# Load ammo templates
AMMO_DIR = Path("ammo")
TARGETS_DIR = Path("targets")

def load_ammo_categories():
    """Parse all ammo templates by category"""
    categories = {}
    if not AMMO_DIR.exists():
        return categories
    
    for category_dir in AMMO_DIR.iterdir():
        if category_dir.is_dir() and not category_dir.name.startswith('.'):
            category_name = category_dir.name
            templates = []
            
            for template_file in category_dir.glob("*.yaml"):
                try:
                    with open(template_file, 'r', encoding='utf-8') as f:
                        data = yaml.safe_load(f)
                        templates.append({
                            'name': template_file.stem,
                            'path': str(template_file),
                            'description': data.get('meta', {}).get('description', ''),
                            'severity': data.get('meta', {}).get('severity', 'medium')
                        })
                except:
                    pass
            
            if templates:
                categories[category_name] = templates
    
    return categories

def load_targets():
    """Get available target adapters"""
    targets = []
    if TARGETS_DIR.exists():
        for target_file in TARGETS_DIR.glob("*.py"):
            if target_file.stem != '__init__':
                targets.append(target_file.stem)
    return targets

@app.route('/')
def index():
    """Main UI"""
    return render_template('index.html')

@app.route('/api/config')
def get_config():
    """Get available ammo and targets"""
    return jsonify({
        'ammo': load_ammo_categories(),
        'targets': load_targets(),
        'status': 'ready'
    })

@app.route('/api/attack', methods=['POST'])
def run_attack():
    """Execute attack with selected parameters"""
    data = request.json
    
    target_base = data.get('target_base')
    target_key = data.get('target_key')
    target_model = data.get('target_model')
    ammo_path = data.get('ammo_path')
    
    if not all([target_base, target_key, target_model, ammo_path]):
        return jsonify({'error': 'Missing required parameters'}), 400
    
    # Set environment
    env = os.environ.copy()
    env['TARGET_BASE'] = target_base
    env['TARGET_KEY'] = target_key
    env['TARGET_MODEL'] = target_model
    
    def generate():
        """Stream attack output"""
        try:
            # Run the runner script with selected ammo
            proc = subprocess.Popen(
                [sys.executable, 'runner/run_battery.py', 'single', '--ammo', ammo_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                env=env,
                text=True,
                bufsize=1
            )
            
            for line in proc.stdout:
                yield f"data: {json.dumps({'line': line.strip()})}\n\n"
            
            proc.wait()
            yield f"data: {json.dumps({'done': True, 'code': proc.returncode})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return Response(generate(), mimetype='text/event-stream')

@app.route('/api/probe', methods=['POST'])
def run_probe():
    """Run probe matrix analysis"""
    data = request.json
    
    target_base = data.get('target_base')
    target_key = data.get('target_key')
    models = data.get('models', 'gpt-4')
    efforts = data.get('efforts', 'off,high')
    
    env = os.environ.copy()
    env['PROBE_BASE'] = target_base
    env['PROBE_KEY'] = target_key
    
    def generate():
        try:
            proc = subprocess.Popen(
                [sys.executable, 'tools/probe.py', '--models', models, '--efforts', efforts],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                env=env,
                text=True,
                bufsize=1
            )
            
            for line in proc.stdout:
                yield f"data: {json.dumps({'line': line.strip()})}\n\n"
            
            proc.wait()
            yield f"data: {json.dumps({'done': True, 'code': proc.returncode})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return Response(generate(), mimetype='text/event-stream')

@app.route('/healthz')
def health():
    """Health check for Railway"""
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
