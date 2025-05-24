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
REFERENCE_FASTA = '/tmp/reference/reference.fa'
ANNOTATION_CSV = '/tmp/reference/Axiom_Annotation.r1.csv'
REFERENCE_URL = 'https://download1324.mediafire.com/a5k1ijo792kgANBj6mpPm_aeTwskLeQr6ybzgeT0uW2wIsq0yCr5zMccSWY4kQDpnaTPFRCKUCAoelO9Oi4p8GkCQRQgsaUe3-Pm7ksHA3xLH_QFi7zSRkeM7WNuk0MQWolLUrkrMxZ8Zzs_2PG_aUCp10MGiIy-RhIwqbYxQeUOBw/l2nuwhg89bbtnwj/reference.fa'
ANNOTATION_URL = 'https://download937.mediafire.com/7m7wrexnhnbgUTGI1TBTE8SGS5lOyEVSddDkEFuWA0FD4QDdq039jTvD1rKuPYTtUQebZSnImUOoLIK_70UiMWj9gkyYokw04KN0ZpPpkZ0y29IjK3b93LiiaiZ76_jpwHPdGEyqihouxrO_3CQsswEZRCGB8ZjKI91WAOqK7Vo3iA/p5iapfestqmk0e8/Axiom_Annotation.r1.csv'

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

        # Download apt-cel-convert if needed
        runtime_bin = "/tmp/bin/apt-cel-convert"
        if not os.path.exists(runtime_bin):
            os.makedirs("/tmp/bin", exist_ok=True)
            subprocess.run(["cp", "binaries/apt-cel-convert", runtime_bin], check=True)
            subprocess.run(["chmod", "+x", runtime_bin], check=True)
            print("[DEBUG] Copied apt-cel-convert binary to /tmp/bin")

        # Ensure reference.fa exists
        if not os.path.exists(REFERENCE_FASTA):
            print("[INFO] Downloading reference.fa...")
            urllib.request.urlretrieve(REFERENCE_URL, REFERENCE_FASTA)

        # Ensure Axiom_Annotation.r1.csv exists
        if not os.path.exists(ANNOTATION_CSV):
            print("[INFO] Downloading Axiom_Annotation.r1.csv...")
            urllib.request.urlretrieve(ANNOTATION_URL, ANNOTATION_CSV)

        cel_list_path = os.path.join(UPLOAD_FOLDER, "cel-files.txt")
        with open(cel_list_path, "w") as f:
            f.write(cel_path + "\n")

        # Time step 1
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

        # Time step 2
        vcf_path = cel_path.replace('.CEL', '.vcf')
        start = time.time()
        subprocess.run([
            'bcftools', '+gtc2vcf',
            '--chps', chp_path,
            '--fasta-ref', REFERENCE_FASTA,
            '--annotation-files', ANNOTATION_CSV,
            '-o', vcf_path
        ], check=True)
        print(f"[DEBUG] gtc2vcf took {time.time() - start:.2f} seconds")

        if not os.path.exists(vcf_path):
            raise FileNotFoundError(f"VCF file not found: {vcf_path}")

        # Time step 3
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
