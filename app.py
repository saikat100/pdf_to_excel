from flask import Flask, render_template, request, send_file, jsonify
import os
from werkzeug.utils import secure_filename
from converter import convert_pdf_to_excel
import uuid

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'outputs'
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024  # 32MB limit

# Ensure folders exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and file.filename.lower().endswith('.pdf'):
        session_id = str(uuid.uuid4())
        filename = secure_filename(file.filename)
        pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{session_id}_{filename}")
        excel_filename = filename.rsplit('.', 1)[0] + ".xlsx"
        excel_path = os.path.join(app.config['OUTPUT_FOLDER'], f"{session_id}_{excel_filename}")
        
        file.save(pdf_path)
        
        try:
            success = convert_pdf_to_excel(pdf_path, excel_path)
            if success:
                return jsonify({
                    'message': 'Conversion successful',
                    'download_url': f'/download/{session_id}_{excel_filename}'
                })
            else:
                return jsonify({'error': 'No data found in PDF'}), 400
        except Exception as e:
            return jsonify({'error': f'Conversion failed: {str(e)}'}), 500
        finally:
            # Optional: Clean up uploaded PDF
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
    
    return jsonify({'error': 'Invalid file type. Please upload a PDF.'}), 400

@app.route('/download/<filename>')
def download_file(filename):
    path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
    if os.path.exists(path):
        return send_file(path, as_attachment=True)
    return "File not found", 404

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 10000))
    )
