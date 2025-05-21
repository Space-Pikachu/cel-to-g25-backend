from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import subprocess
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)  # ← temporarily allow all origins for testing

UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
ALLOWED_EXTENSIONS = {'cel'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    return '✅ CEL to G25 backend is live!'


@app.route('/ping')
def ping():
    return 'pong'


@app.route('/convert', methods=['POST'])
def convert():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        file = request.files['file']
        if file.filename == '' or not allowed_file(file.filename):
            return jsonify({'error': 'Invalid or no file selected'}), 400

        filename = secure_filename(file.filename)
        cel_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(cel_path)
        print(f"[DEBUG] Saved CEL file to {cel_path}")

        # ✅ Runtime: Copy apt-cel-convert from repo to /tmp/bin
        runtime_bin = "/tmp/bin/apt-cel-convert"
        if not os.path.exists(runtime_bin):
            os.makedirs("/tmp/bin", exist_ok=True)
            subprocess.run(["cp", "binaries/apt-cel-convert", runtime_bin], check=True)
            subprocess.run(["chmod", "+x", runtime_bin], check=True)
            print("[DEBUG] Copied apt-cel-convert binary to /tmp/bin")

        # 🧪 TEMP DEBUG: Show --help output to confirm flags
        print("[DEBUG] Running apt-cel-convert --help")
        result = subprocess.run([runtime_bin, '--help'], capture_output=True, text=True)
        print(f"[DEBUG] Help Output:\n{result.stdout}\n{result.stderr}")
        return jsonify({"error": "APT binary help output printed to log for debugging"}), 500

    except subprocess.CalledProcessError as sub_err:
        print(f"[ERROR] Subprocess failed: {sub_err}")
        return jsonify({'error': f'Subprocess failed: {str(sub_err)}'}), 500

    except Exception as e:
        print(f"[ERROR] General exception: {e}")
        return jsonify({'error': f'Unexpected server error: {str(e)}'}), 500


@app.route("/health")
def health():
    return {"status": "ok"}, 200


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
