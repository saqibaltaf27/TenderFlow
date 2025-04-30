from fastapi import FastAPI, Form, UploadFile, Request, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from typing import List
import shutil
import os
import tempfile
from PIL import Image
from PyPDF2 import PdfMerger
import logging
from pathlib import Path


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI()


BASE_DIR = os.path.dirname(__file__)
STATIC_DIR = os.path.join(BASE_DIR, "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


UPLOAD_FOLDER = "/tmp"  
REQUIRED_FILES = ['Bid Security.jpg', 'Cover Letter.pdf', 'DRAP.pdf', 'Technical Quotation.pdf']


if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


def allowed_file(filename):
    return filename.split('.')[-1].lower() in {'pdf', 'jpg', 'jpeg', 'png'}


def convert_image_to_pdf(image_path):
    try:
        image = Image.open(image_path).convert("RGB")
        temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        image.save(temp_pdf.name)
        return temp_pdf.name
    except Exception as e:
        logger.error(f"Error converting image to PDF: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error converting image to PDF: {str(e)}")


@app.get("/", response_class=HTMLResponse)
async def read_form(request: Request):

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Tender Generator</title>
        <link rel="stylesheet" href="/static/styles.css">
    </head>
    <body>
        <div class="container">
            <h1>Tender Generator 🧾</h1>
            <form action="/" method="POST" enctype="multipart/form-data">
                <div class="upload-section">
                    <label for="master_file">Upload Master File (PDF):</label>
                    <input type="file" name="master_file" accept=".pdf" required>
                </div>

                <div class="upload-section">
                    <label for="lot_files">Upload Base Files (Multiple PDFs/Images):</label>
                    <input type="file" name="lot_files" accept=".pdf, .jpg, .jpeg, .png" multiple required>
                </div>

                <button type="submit" class="btn-submit">Generate Tender</button>
            </form>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.post("/", response_class=HTMLResponse)
async def upload_files(
    request: Request,
    master_file: UploadFile = Form(...),
    lot_files: List[UploadFile] = Form(...),
):
    try:
       
        if not allowed_file(master_file.filename):
            logger.error(f"Invalid master file: {master_file.filename}")
            return HTMLResponse(content=f"<h1>Invalid master file: {master_file.filename}</h1>")

        master_path = os.path.join(UPLOAD_FOLDER, master_file.filename)
        with open(master_path, "wb") as buffer:
            shutil.copyfileobj(master_file.file, buffer)
            logger.info(f"Master file saved to {master_path}")

       
        lot_paths = []
        for file in lot_files:
            if allowed_file(file.filename):
                path = os.path.join(UPLOAD_FOLDER, file.filename)
                with open(path, "wb") as f:
                    shutil.copyfileobj(file.file, f)
                    logger.info(f"Lot file saved to {path}")
                lot_paths.append(path)

   
        missing = [f for f in REQUIRED_FILES if not any(f.lower() in p.lower() for p in lot_paths)]
        if missing:
            logger.error(f"Missing required files: {', '.join(missing)}")
            return HTMLResponse(content=f"<h1>Missing required files: {', '.join(missing)}</h1>")

        
        merger = PdfMerger()
        merger.append(master_path)
        for path in lot_paths:
            if path.endswith((".jpg", ".jpeg", ".png")):
                pdf_path = convert_image_to_pdf(path)
                merger.append(pdf_path)
            else:
                merger.append(path)

        output_path = os.path.join(UPLOAD_FOLDER, "Generated_Tender.pdf")
        merger.write(output_path)
        merger.close()

        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Tender Generated</title>
            <link rel="stylesheet" href="/static/styles.css">
        </head>
        <body>
            <div class="container">
                <h2>Tender Generated!</h2>
                <a href="/uploads/Generated_Tender.pdf" download>
                    <button class="btn-download">Download Tender</button>
                </a>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content)

    except Exception as e:
        logger.error(f"Error during file upload or PDF generation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


@app.get("/uploads/{filename}", response_class=FileResponse)
async def get_file(filename: str):
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(file_path):
        logger.error(f"File not found: {filename}")
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path=file_path, filename=filename)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)