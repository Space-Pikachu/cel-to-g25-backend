from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import subprocess
from werkzeug.utils import secure_filename
import urllib.request
import time

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
ALLOWED_EXTENSIONS = {'cel'}
REFERENCE_URL = 'https://download1324.mediafire.com/nhricwu77wegZxA1GMSUGXpGRWEnx_v_eMLcYjVAY8y2vsEp-wWweGimw1kZsZulPwAivyzOq-9zo8fAtsjEi4WeQjb_n-PsCEIR9YdChHBvaSkU_FlEVxSfH27Bs3N40xpGeMT0enKJZOQQK2J8FOJOdl1MNNJY1xdtoY-0RUaTY6k/l2nuwhg89bbtnwj/reference.fa'
ANNOTATION_URL = 'https://download937.mediafire.com/yi7a10tfdiegcTL9sDFOE7HgWftKxRki10oDadPEYuqZe3yQpOmGwRj9qDHYz55wuLoklbaWFKEw49u1NLTBhlVfLxb8xc1RvJwtUJ8NG5Lg02eMdcmYnpYgb6wPGYTqKjoLYgLaSGVKcC1I1JBW1EiBS12ZxJrClJ7MZpPtUCy10Xs/p5iapfestqmk0e8/Axiom_Annotation.r1.csv'
REFERENCE_FASTA_PATH = '/tmp/reference/reference.fa'
ANNOTATION_CSV_PATH = '/tmp/reference/Axiom_Annotation.r1.csv'

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

        runtime_bin = "/tmp/bin/apt-cel-convert"
        if not os.path.exists(runtime_bin):
            os.makedirs("/tmp/bin", exist_ok=True)
            subprocess.run(["cp", "binaries/apt-cel-convert", runtime_bin], check=True)
            subprocess.run(["chmod", "+x", runtime_bin], check=True)
            print("[DEBUG] Copied apt-cel-convert binary to /tmp/bin")

        os.makedirs('/tmp/reference', exist_ok=True)
        if not os.path.exists(REFERENCE_FASTA_PATH):
            print("[INFO] Downloading reference.fa...")
            urllib.request.urlretrieve(REFERENCE_URL, REFERENCE_FASTA_PATH)

        if not os.path.exists(ANNOTATION_CSV_PATH):
            print("[INFO] Downloading Axiom_Annotation.r1.csv...")
            urllib.request.urlretrieve(ANNOTATION_URL, ANNOTATION_CSV_PATH)

        cel_list_path = os.path.join(UPLOAD_FOLDER, "cel-files.txt")
        with open(cel_list_path, "w") as f:
            f.write(cel_path + "\n")

        chp_path = cel_path.replace('.CEL', '.CHP')
        start = time.time()
        subprocess.run([
            runtime_bin,
            "--format", "xda",
            "--out-dir", UPLOAD_FOLDER,
            "--cel-files", cel_list_path
        ], check=True)
        print(f"[DEBUG] apt-cel-convert took {time.time() - start:.2f} seconds")

        if not os.path.exists(chp_path):
            raise FileNotFoundError(f"CHP file not found: {chp_path}")

        vcf_path = cel_path.replace('.CEL', '.vcf')
        start = time.time()
        subprocess.run([
            'bcftools', '+gtc2vcf',
            '--chps', chp_path,
            '--fasta-ref', REFERENCE_FASTA_PATH,
            '--annotation-files', ANNOTATION_CSV_PATH,
            '-o', vcf_path
        ], check=True)
        print(f"[DEBUG] gtc2vcf took {time.time() - start:.2f} seconds")

        if not os.path.exists(vcf_path):
            raise FileNotFoundError(f"VCF file not found: {vcf_path}")

        txt_path = cel_path.replace('.CEL', '.txt')
        start = time.time()
        subprocess.run(['python3', 'vcf_to_23andme.py', vcf_path, txt_path], check=True)
        print(f"[DEBUG] vcf_to_23andme took {time.time() - start:.2f} seconds")

        if not os.path.exists(txt_path):
            raise FileNotFoundError(f"TXT file not found: {txt_path}")

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
