from fastapi import FastAPI, Form, UploadFile, Request, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from typing import List
import shutil
import os
import tempfile
from PIL import Image
from PyPDF2 import PdfMerger
import pypandoc
import logging
from pathlib import Path

# Setup
app = FastAPI()
BASE_DIR = os.path.dirname(__file__)
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
STATIC_DIR = os.path.join(BASE_DIR, "static")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Logging
logging.basicConfig(level=logging.INFO)

# Helpers
def is_image(filename): return filename.lower().endswith((".jpg", ".jpeg", ".png"))
def is_word(filename): return filename.lower().endswith(".docx")

def convert_image_to_pdf(image_path):
    img = Image.open(image_path).convert("RGB")
    temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    img.save(temp_pdf.name)
    return temp_pdf.name

def convert_word_to_pdf(docx_path):
    temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    output_path = temp_pdf.name
    try:
        pypandoc.convert_file(docx_path, 'pdf', outputfile=output_path)
        return output_path
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Word to PDF conversion failed: {e}")

# Routes
@app.get("/", response_class=HTMLResponse)
async def index():
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>Tender Generator</title>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: #f4f7f9;
                margin: 0; padding: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
            }
            .container {
                background: white;
                padding: 2rem 3rem;
                box-shadow: 0 8px 20px rgba(0,0,0,0.1);
                border-radius: 10px;
                max-width: 480px;
                width: 100%;
                text-align: center;
            }
            h1 {
                margin-bottom: 1.5rem;
                color: #333;
            }
            label {
                display: block;
                margin-top: 1rem;
                margin-bottom: 0.5rem;
                font-weight: 600;
                color: #555;
                text-align: left;
            }
            input[type="file"] {
                width: 100%;
                padding: 0.3rem;
                border-radius: 5px;
                border: 1px solid #ccc;
                font-size: 0.9rem;
            }
            button {
                margin-top: 1.8rem;
                background-color: #007bff;
                border: none;
                color: white;
                padding: 0.75rem 1.5rem;
                font-size: 1rem;
                font-weight: 600;
                border-radius: 6px;
                cursor: pointer;
                transition: background-color 0.3s ease;
            }
            button:hover {
                background-color: #0056b3;
            }
            .footer {
                margin-top: 1.5rem;
                font-size: 0.8rem;
                color: #999;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📄 Tender Generator</h1>
            <form action="/" method="post" enctype="multipart/form-data">
                <label for="master_file">Master PDF File:</label>
                <input id="master_file" type="file" name="master_file" accept=".pdf" required />

                <label for="lot_files">Lot Files (PDF, Word, Images):</label>
                <input id="lot_files" type="file" name="lot_files" accept=".pdf,.docx,.jpg,.jpeg,.png" multiple required />

                <button type="submit">Generate Tender</button>
            </form>
            <div class="footer">Made with ❤️ using FastAPI</div>
        </div>
    </body>
    </html>
    """)

@app.post("/", response_class=HTMLResponse)
async def upload(
    request: Request,
    master_file: UploadFile = Form(...),
    lot_files: List[UploadFile] = Form(...),
):
    try:
        merger = PdfMerger()

        # Save and append master file first
        temp_master = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        shutil.copyfileobj(master_file.file, temp_master)
        temp_master.close()
        merger.append(temp_master.name)

        # Process and append lot files
        for file in lot_files:
            if not file.filename:
                raise HTTPException(status_code=400, detail="One of the uploaded files is missing a filename.")
            
            suffix = Path(file.filename).suffix or ".pdf"
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
            shutil.copyfileobj(file.file, temp_file)
            temp_file.close()

            if is_image(file.filename):
                pdf_path = convert_image_to_pdf(temp_file.name)
                merger.append(pdf_path)
            elif is_word(file.filename):
                pdf_path = convert_word_to_pdf(temp_file.name)
                merger.append(pdf_path)
            else:
                # Assume PDF
                merger.append(temp_file.name)

        # Save final merged PDF to uploads folder
        output_file = os.path.join(UPLOAD_FOLDER, "Generated_Tender.pdf")
        merger.write(output_file)
        merger.close()

        # Return download page
        return HTMLResponse(content=f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <title>Tender Generated</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background: #f4f7f9;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                }}
                .container {{
                    background: white;
                    padding: 2rem 3rem;
                    box-shadow: 0 8px 20px rgba(0,0,0,0.1);
                    border-radius: 10px;
                    text-align: center;
                    max-width: 400px;
                    width: 100%;
                }}
                h2 {{
                    color: #28a745;
                }}
                a button {{
                    background-color: #007bff;
                    border: none;
                    color: white;
                    padding: 0.75rem 1.5rem;
                    font-size: 1rem;
                    font-weight: 600;
                    border-radius: 6px;
                    cursor: pointer;
                    transition: background-color 0.3s ease;
                }}
                a button:hover {{
                    background-color: #0056b3;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>✅ Tender Merged Successfully</h2>
                <a href="/uploads/Generated_Tender.pdf" download>
                    <button>Download Tender</button>
                </a>
            </div>
        </body>
        </html>
        """)

    except Exception as e:
        logging.exception("Error in processing:")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/uploads/{filename}", response_class=FileResponse)
async def serve_file(filename: str):
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path, filename=filename)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
