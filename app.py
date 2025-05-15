# file: app.py

from flask import Flask, request, jsonify, send_file
import os
from werkzeug.utils import secure_filename
import subprocess
import pandas as pd
from sklearn.preprocessing import StandardScaler

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'cel', 'CEL'}

app = Flask(__name__)
@app.route('/')
def index():
    return '✅ CEL to G25 backend is live!'

@app.route('/ping')
def ping():
    return 'pong'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Check valid file extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Convert CEL to VCF
def convert_cel_to_vcf(cel_path, vcf_path):
    subprocess.run(['apt-cel-convert', '-i', cel_path, '-o', vcf_path], check=True)

# Project VCF to G25 using external pipeline (placeholder)
def project_to_g25(vcf_path, out_txt, ref_panel):
    subprocess.run(['qpAdm', '-p', ref_panel, '-g', vcf_path, '-o', out_txt], check=True)

# Normalize the G25 coordinates
def normalize_coordinates(input_txt):
    df = pd.read_csv(input_txt, delim_whitespace=True)
    scaler = StandardScaler()
    scaled = scaler.fit_transform(df.iloc[:, 1:])
    scaled_df = pd.DataFrame(scaled, columns=df.columns[1:])
    scaled_df.insert(0, df.columns[0], df.iloc[:, 0])
    out_path = input_txt.replace(".txt", "_scaled.csv")
    scaled_df.to_csv(out_path, index=False)
    return out_path

@app.route('/convert', methods=['POST'])
def convert():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        cel_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(cel_path)

        vcf_path = cel_path.replace('.CEL', '.vcf')
        g25_txt = cel_path.replace('.CEL', '_g25.txt')
        ref_panel = 'reference.par'  # You need to provide this file

        try:
            convert_cel_to_vcf(cel_path, vcf_path)
            project_to_g25(vcf_path, g25_txt, ref_panel)
            scaled_path = normalize_coordinates(g25_txt)
        except subprocess.CalledProcessError as e:
            return jsonify({'error': str(e)}), 500

        return jsonify({
            'g25_unscaled': g25_txt,
            'g25_scaled': scaled_path
        })
    else:
        return jsonify({'error': 'Invalid file type'}), 400

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

