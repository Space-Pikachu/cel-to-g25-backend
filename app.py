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
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({'error': 'Invalid or no file selected'}), 400

    filename = secure_filename(file.filename)
    cel_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(cel_path)

    # Step 1: Run APT Tools to generate CHP
    chp_path = cel_path.replace('.CEL', '.CHP')
    subprocess.run(['/usr/local/bin/apt-cel-convert', '-o', UPLOAD_FOLDER, '-a', 'AxiomGT1', cel_path], check=True)

    # Step 2: Convert CHP to VCF using gtc2vcf via bcftools plugin
    vcf_path = cel_path.replace('.CEL', '.vcf')
    subprocess.run([
        'bcftools', '+gtc2vcf',
        '--chps', chp_path,
        '--fasta-ref', 'reference.fasta',
        '--annotation-files', 'Axiom_Annotation.r1.csv',
        '-o', vcf_path
    ], check=True)

    # Step 3: Convert VCF to 23andMe TXT
    txt_path = cel_path.replace('.CEL', '.txt')
    subprocess.run(['python3', 'vcf_to_23andme.py', vcf_path, txt_path], check=True)

    return send_file(txt_path, as_attachment=True)


@app.route("/health")
def health():
    return {"status": "ok"}, 200


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
