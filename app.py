from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import subprocess
from werkzeug.utils import secure_filename
import urllib.request

app = Flask(__name__)
CORS(app)  # ← temporarily allow all origins for testing

UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
ALLOWED_EXTENSIONS = {'cel'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

ANNOTATION_URL = "https://download937.mediafire.com/7m7wrexnhnbgUTGI1TBTE8SGS5lOyEVSddDkEFuWA0FD4QDdq039jTvD1rKuPYTtUQebZSnImUOoLIK_70UiMWj9gkyYokw04KN0ZpPpkZ0y29IjK3b93LiiaiZ76_jpwHPdGEyqihouxrO_3CQsswEZRCGB8ZjKI91WAOqK7Vo3iA/p5iapfestqmk0e8/Axiom_Annotation.r1.csv"
REFERENCE_URL = "https://download1324.mediafire.com/a5k1ijo792kgANBj6mpPm_aeTwskLeQr6ybzgeT0uW2wIsq0yCr5zMccSWY4kQDpnaTPFRCKUCAoelO9Oi4p8GkCQRQgsaUe3-Pm7ksHA3xLH_QFi7zSRkeM7WNuk0MQWolLUrkrMxZ8Zzs_2PG_aUCp10MGiIy-RhIwqbYxQeUOBw/l2nuwhg89bbtnwj/reference.fa"

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

        # ✅ Step 0: Download reference and annotation files if needed
        reference_path = "reference.fa"
        if not os.path.exists(reference_path):
            print("[INFO] Downloading reference.fa...")
            urllib.request.urlretrieve(REFERENCE_URL, reference_path)
            print("[INFO] reference.fa downloaded")

        annotation_path = "Axiom_Annotation.r1.csv"
        if not os.path.exists(annotation_path):
            print("[INFO] Downloading Axiom_Annotation.r1.csv...")
            urllib.request.urlretrieve(ANNOTATION_URL, annotation_path)
            print("[INFO] Axiom_Annotation.r1.csv downloaded")

        # ✅ Write CEL file path to temp file for apt-cel-convert
        cel_list_path = os.path.join(UPLOAD_FOLDER, "cel-files.txt")
        with open(cel_list_path, "w") as f:
            f.write(cel_path + "\n")

        # ✅ Step 1: Run apt-cel-convert using proper flags
        subprocess.run([
            runtime_bin,
            "--format", "xda",
            "--out-dir", UPLOAD_FOLDER,
            "--cel-files", cel_list_path
        ], check=True)
        print(f"[DEBUG] apt-cel-convert completed using {cel_list_path}")

        # ✅ Step 2: Convert CHP to VCF
        chp_path = cel_path.replace('.CEL', '.CHP')
        vcf_path = cel_path.replace('.CEL', '.vcf')
        subprocess.run([
            'bcftools', '+gtc2vcf',
            '--chps', chp_path,
            '--fasta-ref', reference_path,
            '--annotation-files', annotation_path,
            '-o', vcf_path
        ], check=True)
        print(f"[DEBUG] Converted VCF file at {vcf_path}")

        # ✅ Step 3: Convert VCF to TXT
        txt_path = cel_path.replace('.CEL', '.txt')
        subprocess.run(['python3', 'vcf_to_23andme.py', vcf_path, txt_path], check=True)
        print(f"[DEBUG] Converted TXT file at {txt_path}")

        return send_file(txt_path, as_attachment=True)

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
