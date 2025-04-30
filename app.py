import os
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash
from PyPDF2 import PdfMerger
from PIL import Image
import tempfile
import shutil

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = '/tmp' 
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'jpg', 'jpeg', 'png'}
app.secret_key = 'ce920-212' 

REQUIRED_FILES = ['Bid Security.jpg', 'Cover Letter.pdf', 'DRAP.pdf', 'Technical Quotation.pdf']

# Ensure upload folder exists
#if not os.path.exists(app.config['UPLOAD_FOLDER']):
    #os.makedirs(app.config['UPLOAD_FOLDER'])

# Helper function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Helper function to convert image to PDF
def convert_image_to_pdf(image_path):
    try:
        image = Image.open(image_path).convert("RGB")
        temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        image.save(temp_pdf.name)
        return temp_pdf.name
    except Exception as e:
        return None

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Upload master file
        master_file = request.files.get('master_file')
        lot_files = request.files.getlist('lot_files')

        # Check if master file is uploaded
        if master_file and allowed_file(master_file.filename):
            master_file_path = os.path.join(app.config['UPLOAD_FOLDER'], master_file.filename)
            master_file.save(master_file_path)
        else:
            flash('Please upload a valid master file (PDF).', 'error')
            return redirect(request.url)

        # Check if lot files are uploaded and valid
        lot_file_paths = []
        for file in lot_files:
            if file and allowed_file(file.filename):
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
                file.save(file_path)
                lot_file_paths.append(file_path)
            else:
                flash('Some lot files are not valid. Please upload PDF or image files only.', 'error')
                return redirect(request.url)

        # Validate that all required files are present
        missing_files = [f for f in REQUIRED_FILES if not any(f.lower() in path.lower() for path in lot_file_paths)]
        if missing_files:
            flash(f'Missing required files: {", ".join(missing_files)}', 'error')
            return redirect(request.url)

        # Merge the PDF files
        try:
            merger = PdfMerger()
            merger.append(master_file_path)

            for file_path in lot_file_paths:
                if file_path.lower().endswith(('.jpg', '.jpeg', '.png')):
                    pdf_file = convert_image_to_pdf(file_path)
                    if pdf_file:
                        merger.append(pdf_file)
                else:
                    merger.append(file_path)

            output_path = os.path.join('/tmp', 'Generated_Tender.pdf')
            merger.write(output_path)
            merger.close()

            return render_template('index.html', filename='Generated_Tender.pdf')

        except Exception as e:
            flash(f'Error generating tender: {e}', 'error')
            return redirect(request.url)

    return render_template('index.html')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
   return send_from_directory('/tmp', filename)

if __name__ == '__main__':
    app.run(debug=True)
