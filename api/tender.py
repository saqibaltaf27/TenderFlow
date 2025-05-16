from fastapi import (
    FastAPI, Form, UploadFile, Request, HTTPException, Depends, status, Response, BackgroundTasks # Added BackgroundTasks
)
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from typing import List
import shutil
import os
import tempfile
from PIL import Image
from PyPDF2 import PdfMerger # Corrected: PdfWriter is preferred for new code, but PdfMerger is what you used and works.
import pypandoc
import logging
from pathlib import Path
import secrets 
import uvicorn


app = FastAPI()

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


logging.basicConfig(level=logging.INFO)


VALID_USERNAME = "crm"
VALID_PASSWORD = "Inst@2025"

def is_image(filename): return filename.lower().endswith((".jpg", ".jpeg", ".png"))
def is_word(filename): return filename.lower().endswith(".docx")

# --- Helper function for cleanup ---
def cleanup_temp_dir(temp_dir_path: str):
    logging.info(f"Cleaning up temporary directory: {temp_dir_path}")
    try:
        # Delete all files within the directory first
        for f_path in Path(temp_dir_path).glob("*"):
            try:
                f_path.unlink()
                logging.info(f"Deleted temporary file: {f_path}")
            except OSError as e:
                logging.error(f"Error deleting temporary file {f_path}: {e}")
       
        Path(temp_dir_path).rmdir()
        logging.info(f"Removed temporary directory: {temp_dir_path}")
    except OSError as e:
        logging.error(f"Error removing temporary directory {temp_dir_path}: {e}")
    except Exception as e:
        logging.error(f"Unexpected error during cleanup of {temp_dir_path}: {e}")


def convert_image_to_pdf(image_path):
    img = Image.open(image_path)
    # Ensure RGB for saving as PDF if it's RGBA or P (palette)
    if img.mode == 'RGBA' or img.mode == 'P':
        img = img.convert("RGB")
    temp_pdf_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    img.save(temp_pdf_file.name)
    temp_pdf_file.close() # Close the file handle
    return temp_pdf_file.name

def convert_word_to_pdf(docx_path):
    temp_pdf_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    output_path = temp_pdf_file.name
    temp_pdf_file.close() # Close the file handle before pandoc tries to write to it.
    try:
        pypandoc.convert_file(docx_path, 'pdf', outputfile=output_path)
        return output_path
    except Exception as e:
        
        if os.path.exists(output_path):
            os.unlink(output_path)
        raise HTTPException(status_code=500, detail=f"Word to PDF conversion failed for {Path(docx_path).name}: {e}")

def check_authentication(request: Request):
    auth_cookie = request.cookies.get("authenticated")
    if auth_cookie != "true":
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER, 
            detail="Not authenticated",
            headers={"Location": "/"}, # Redirect to login page
        )

@app.get("/", response_class=HTMLResponse)
async def login_page():
    return HTMLResponse("""
    <html>
    <head>
        <title>Login - Tender Generator</title>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #6B73FF 0%, #000DFF 100%);
                display: flex;
                height: 100vh;
                justify-content: center;
                align-items: center;
                margin: 0;
                color: white;
            }
            .login-card {
                background: rgba(255,255,255,0.15);
                backdrop-filter: blur(10px);
                padding: 2rem 3rem;
                border-radius: 15px;
                box-shadow: 0 8px 20px rgba(0,0,0,0.3);
                width: 320px;
                text-align: center;
                border: 1px solid rgba(255,255,255,0.3);
            }
            h2 {
                margin-bottom: 1.5rem;
                color: #ffffff;
                text-shadow: 0 0 8px rgba(255,255,255,0.8); /* Glow effect */
                font-family: 'Roboto', sans-serif;  /* Modern font */
                letter-spacing: 0.5px;
            }
            input[type=text], input[type=password] {
                width: 100%;
                padding: 12px 15px;
                margin: 10px 0 20px 0;
                border: none;
                border-radius: 8px;
                font-size: 1rem;
                outline: none;
                background-color: rgba(255,255,255,0.8); /* Slightly lighter input fields */
                color: #333;
                box-sizing: border-box; /* Ensure padding doesn't add to width */
            }
            input[type=text]:focus, input[type=password]:focus {
                box-shadow: 0 0 12px 3px rgba(0, 149, 237, 0.5); /* Focus glow */
                background-color: rgba(255,255,255,0.95);
            }
            button {
                background: linear-gradient(to right, #667eea, #764ba2); /* Gradient button */
                color: white;
                border: none;
                padding: 12px 20px;
                width: 100%;
                border-radius: 8px;
                font-size: 1.1rem;
                cursor: pointer;
                transition: all 0.3s ease;
                font-weight: 500; /* Medium font weight */
                box-shadow: 0 4px 12px rgba(0,0,0,0.2);
                letter-spacing: 1px;
            }
            button:hover {
                background: linear-gradient(to right, #6a11cb, #2575fc);
                transform: translateY(-2px);
                box-shadow: 0 6px 15px rgba(0,0,0,0.3);
            }
            .error {
                color: #ff4c4c;
                margin-bottom: 15px;
                font-weight: 500;
                text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
            }
        </style>
        <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap" rel="stylesheet">
    </head>
    <body>
        <div class="login-card">
            <h2>Tender Generator Login</h2>
            <form method="post" action="/login">
                <input name="username" type="text" placeholder="Username" required autocomplete="off">
                <input name="password" type="password" placeholder="Password" required autocomplete="off">
                <button type="submit">Login</button>
            </form>
        
                        </div>
    </body>
    </html>
    """)

@app.post("/login", response_class=HTMLResponse) 
async def login(response: Response, username: str = Form(...), password: str = Form(...)):
    if username == VALID_USERNAME and password == VALID_PASSWORD:
        redirect_response = RedirectResponse(url="/upload", status_code=status.HTTP_302_FOUND)
        redirect_response.set_cookie(key="authenticated", value="true", httponly=True, max_age=3600, samesite="lax") # 1 hour session
        return redirect_response
    else:
        return HTMLResponse("""
        <html>
        <head>
            <title>Login Failed</title>
            <style>
                body {
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background: linear-gradient(135deg, #6B73FF 0%, #000DFF 100%);
                    display: flex;
                    height: 100vh;
                    justify-content: center;
                    align-items: center;
                    margin: 0;
                    color: white;
                }
                .login-card {
                    background: rgba(255,255,255,0.15);
                    backdrop-filter: blur(10px);
                    padding: 2rem 3rem;
                    border-radius: 15px;
                    box-shadow: 0 8px 20px rgba(0,0,0,0.3);
                    width: 320px;
                    text-align: center;
                    border: 1px solid rgba(255,255,255,0.3);
                }
                h2 {
                    margin-bottom: 1.5rem;
                    color: white;
                    text-shadow: 0 0 8px rgba(255,255,255,0.8); /* Glow effect */
                    font-family: 'Roboto', sans-serif;  /* Modern font */
                    letter-spacing: 0.5px;
                }
                input[type=text], input[type=password] {
                    width: 100%;
                    padding: 12px 15px;
                    margin: 10px 0 20px 0;
                    border: none;
                    border-radius: 8px;
                    font-size: 1rem;
                    outline: none;
                    background-color: rgba(255,255,255,0.8); /* Slightly lighter input fields */
                    color: #333;
                    box-sizing: border-box;
                }
                input[type=text]:focus, input[type=password]:focus {
                    box-shadow: 0 0 12px 3px rgba(0, 149, 237, 0.5); /* Focus glow */
                    background-color: rgba(255,255,255,0.95);
                }
                button {
                    background: linear-gradient(to right, #667eea, #764ba2); /* Gradient button */
                    color: white;
                    border: none;
                    padding: 12px 20px;
                    width: 100%;
                    border-radius: 8px;
                    font-size: 1.1rem;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    font-weight: 500; /* Medium font weight */
                    box-shadow: 0 4px 12px rgba(0,0,0,0.2);
                    letter-spacing: 1px;
                }
                button:hover {
                    background: linear-gradient(to right, #6a11cb, #2575fc);
                    transform: translateY(-2px);
                    box-shadow: 0 6px 15px rgba(0,0,0,0.3);
                }
                .error {
                    color: #ff4c4c; /* Brighter red for error */
                    margin-bottom: 15px;
                    font-weight: 500;
                    text-shadow: 1px 1px 2px rgba(0,0,0,0.3); /* Subtle shadow for readability */
                }
            </style>
            <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap" rel="stylesheet">
        </head>
        <body>
            <div class="login-card">
                <h2>Tender Generator Login</h2>
                <div class="error">Invalid username or password</div>
                <form method="post" action="/login">
                    <input name="username" type="text" placeholder="Username" required autocomplete="off">
                    <input name="password" type="password" placeholder="Password" required autocomplete="off">
                    <button type="submit">Login</button>
                </form>
            </div>
        </body>
        </html>
        """, status_code=401) 

@app.get("/logout")
async def logout():
    redirect_response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    redirect_response.delete_cookie("authenticated", samesite="lax")
    return redirect_response

@app.get("/upload", response_class=HTMLResponse)
async def upload_form(request: Request, _ = Depends(check_authentication)): 
    return HTMLResponse(content=f"""
    <html>
    <head>
        <title>Tender Generator</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                padding: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                color: #333;
                /* Professional office environment background */
                background: linear-gradient(135deg, #e6ebf1, #cbd4db); /* Soft blue-gray gradient */
                /* optionally add a subtle texture or pattern here if desired */
            }}
            .container {{
                background: white;
                border-radius: 20px;
                padding: 3rem 3.5rem 5rem 3.5rem; /* extra bottom padding to fit logout button */
                width: 500px;
                box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
                position: relative;
            }}
            h1 {{
                font-weight: 800;
                font-size: 2.5rem;
                margin-bottom: 2rem;
                text-align: center;
                color: #D72631;
                font-family: 'Montserrat', sans-serif;
                letter-spacing: -0.02em;
            }}
            label {{
                font-weight: 600;
                display: block;
                margin: 1.2rem 0 0.5rem 0;
                color: #555;
            }}
            input[type=file] {{
                width: 100%;
                padding: 12px 15px;
                border-radius: 12px;
                border: 1px solid #ddd;
                font-size: 1.1rem;
                cursor: pointer;
                transition: all 0.3s ease;
                background-color: #fff;
                color: #333;
                box-sizing: border-box;
            }}
            input[type=file]:hover {{
                border-color: #D72631;
                box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
            }}
            button[type=submit] {{ /* Target specifically the submit button */
                margin-top: 2.5rem;
                width: 100%;
                background-color: #D72631;
                color: white;
                font-size: 1.3rem;
                font-weight: 700;
                padding: 15px 0;
                border: none;
                border-radius: 15px;
                cursor: pointer;
                transition: background-color 0.3s ease, transform 0.2s ease;
                font-family: 'Roboto', sans-serif;
                letter-spacing: 0.5px;
                box-shadow: 0 5px 10px rgba(0, 0, 0, 0.1);
            }}
            button[type=submit]:hover {{ /* Target specifically the submit button */
                background-color: #c8232b;
                transform: translateY(-2px);
                box-shadow: 0 7px 12px rgba(0, 0, 0, 0.15);
            }}
            .logout-btn {{
                position: absolute;
                bottom: 20px; /* move to bottom inside container */
                left: 50%; /* center horizontally */
                transform: translateX(-50%);
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 14px; /* smaller padding */
                border-radius: 10px;
                cursor: pointer;
                font-weight: 600;
                font-size: 0.85rem; /* smaller font */
                transition: background-color 0.3s ease, transform 0.2s ease;
                font-family: 'Roboto', sans-serif;
                box-shadow: 0 3px 6px rgba(0, 0, 0, 0.1);
                width: auto; /* Allow button to size to content */
                min-width: 100px; /* Ensure minimum width */
                margin-top: 1rem; /* Add some margin from the submit button */
            }}
            .logout-btn:hover {{
                background-color: #45a049;
                transform: translate(-50%, -2px);
                box-shadow: 0 5px 8px rgba(0, 0, 0, 0.15);
            }}
        </style>
        <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700&family=Roboto:wght@400;500;700&display=swap" rel="stylesheet">
    </head>
    <body>
        <div class="container">
            <form action="/upload" method="post" enctype="multipart/form-data">
                
                <h1>📄 Tender Generator</h1>

                <label for="master_file">Master PDF File:</label>
                <input type="file" name="master_file" id="master_file" accept=".pdf" required>

                <label for="lot_files">Lot Files (PDF, JPG, PNG, DOCX):</label>
                <input type="file" name="lot_files" id="lot_files" accept=".pdf,.jpg,.jpeg,.png,.docx" multiple required>

                <button type="submit">Generate Tender Document</button>
                                   
                <button type="button" class="logout-btn" onclick="window.location.href='/logout'">Logout</button>
            </form>
        </div>
    </body>
    </html>
    """)

@app.post("/upload") 
async def upload(
    request: Request, 
    background_tasks: BackgroundTasks,
    master_file: UploadFile = Form(...),
    lot_files: List[UploadFile] = Form(...),
    _ = Depends(check_authentication) 
):

    if not master_file.filename or master_file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Master file must be a PDF and have a filename.")

    temp_dir_path: str = tempfile.mkdtemp() 

    background_tasks.add_task(cleanup_temp_dir, temp_dir_path)

    temporary_file_paths_to_clean = []

    try:
        master_path = os.path.join(temp_dir_path, master_file.filename)
        with open(master_path, "wb") as f:
            shutil.copyfileobj(master_file.file, f) 
        await master_file.close() 

        pdf_merger = PdfMerger()
        pdf_merger.append(master_path)

        for lot_file in lot_files:
            if not lot_file.filename:
                logging.warning("Skipping a lot file with no filename.")
                await lot_file.close()
                continue

            lot_file_path = os.path.join(temp_dir_path, lot_file.filename)
            with open(lot_file_path, "wb") as f:
                shutil.copyfileobj(lot_file.file, f)
            await lot_file.close() 

            ext = lot_file.filename.lower().split('.')[-1] if '.' in lot_file.filename else ""

            converted_pdf_path = None
            if ext == "pdf":
                pdf_merger.append(lot_file_path)
            elif ext in ("jpg", "jpeg", "png"):
                converted_pdf_path = convert_image_to_pdf(lot_file_path)
                pdf_merger.append(converted_pdf_path)
                temporary_file_paths_to_clean.append(converted_pdf_path) 
                # os.unlink(lot_file_path) # Original image can be kept or deleted
            elif ext == "docx":
                converted_pdf_path = convert_word_to_pdf(lot_file_path)
                pdf_merger.append(converted_pdf_path)
                temporary_file_paths_to_clean.append(converted_pdf_path) # Mark for cleanup
                # os.unlink(lot_file_path) # Original docx can be kept or deleted
            else:
                logging.error(f"Unsupported file type: {lot_file.filename}")
                raise HTTPException(status_code=400, detail=f"Unsupported file type: {lot_file.filename}")

        output_pdf_filename = "Tender.pdf" 
        output_pdf_path = os.path.join(temp_dir_path, output_pdf_filename)
        pdf_merger.write(output_pdf_path)
        pdf_merger.close()

        for temp_pdf in temporary_file_paths_to_clean:
            if os.path.exists(temp_pdf):
                try:
                    os.unlink(temp_pdf)
                    logging.info(f"Cleaned up intermediate PDF: {temp_pdf}")
                except OSError as e:
                    logging.error(f"Error cleaning up intermediate PDF {temp_pdf}: {e}")


        
        return FileResponse(
            path=output_pdf_path,
            media_type='application/pdf',
            filename=output_pdf_filename         )

    except HTTPException: 
        raise
    except Exception as e:
        logging.error(f"Error during PDF generation: {e}", exc_info=True)
        
        raise HTTPException(status_code=500, detail=f"An internal error occurred: {str(e)}")
    

#if __name__ == "__main__":

   # uvicorn.run(app, host="127.0.0.1", port=8000)
