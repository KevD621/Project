from flask import Flask, request, jsonify
from sandbox import run_sandbox
from analyzer import analyze
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

@app.route('/check', methods=['POST'])
def check_url():
    data = request.json
    url = data.get('url')
    if not url:
        return jsonify({"error": "URL required"}), 400

    app.logger.info(f"Checking URL: {url}")
    # Run sandbox
    sandbox_result = run_sandbox(url)
    if 'error' in sandbox_result:
        return jsonify({"error": sandbox_result['error']}), 500

    # Analyze
    report = analyze(sandbox_result)
    return jsonify(report)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)