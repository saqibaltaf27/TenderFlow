from fastapi import FastAPI, Form, UploadFile, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import shutil, os, tempfile
from PIL import Image
from PyPDF2 import PdfMerger

app = FastAPI()
templates = Jinja2Templates(directory="templates")
UPLOAD_FOLDER = "/tmp"
REQUIRED_FILES = ['Bid Security.jpg', 'Cover Letter.pdf', 'DRAP.pdf', 'Technical Quotation.pdf']

def allowed_file(filename):
    return filename.split('.')[-1].lower() in {'pdf', 'jpg', 'jpeg', 'png'}

def convert_image_to_pdf(image_path):
    image = Image.open(image_path).convert("RGB")
    temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    image.save(temp_pdf.name)
    return temp_pdf.name

@app.get("/", response_class=HTMLResponse)
async def read_form(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "filename": None})

@app.post("/", response_class=HTMLResponse)
async def upload_files(
    request: Request,
    master_file: UploadFile = Form(...),
    lot_files: list[UploadFile] = Form(...)
):
    if not allowed_file(master_file.filename):
        return templates.TemplateResponse("index.html", {"request": request, "error": "Invalid master file"})

    master_path = os.path.join(UPLOAD_FOLDER, master_file.filename)
    with open(master_path, "wb") as buffer:
        shutil.copyfileobj(master_file.file, buffer)

    lot_paths = []
    for file in lot_files:
        if allowed_file(file.filename):
            path = os.path.join(UPLOAD_FOLDER, file.filename)
            with open(path, "wb") as f:
                shutil.copyfileobj(file.file, f)
            lot_paths.append(path)

    missing = [f for f in REQUIRED_FILES if not any(f.lower() in p.lower() for p in lot_paths)]
    if missing:
        return templates.TemplateResponse("index.html", {"request": request, "error": f"Missing: {', '.join(missing)}"})

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

    return templates.TemplateResponse("index.html", {"request": request, "filename": "Generated_Tender.pdf"})

@app.get("/uploads/{filename}", response_class=FileResponse)
async def get_file(filename: str):
    return FileResponse(path=os.path.join(UPLOAD_FOLDER, filename), filename=filename)
