# TenderFlow - Your Automated Tender Document Generator

[![Railway](https://railway.app/button.svg)](https://railway.app/new/template)

TenderFlow is a web application designed to streamline the process of creating tender documents. It allows users to upload a master PDF file and combine it with multiple lot-specific files (in PDF, JPG, PNG, or DOCX format) to generate a comprehensive tender document.

## Features

* **Master Document Integration:** Upload a base PDF document that serves as the foundation for your tender.
* **Multi-Format Lot Support:** Include supplementary information for different lots by uploading files in various formats (PDF, JPG, PNG, DOCX).
* **Automatic Conversion:** Automatically converts image files (JPG, PNG) and Word documents (DOCX) to PDF format for seamless merging.
* **Secure Access:** Password-protected login to ensure only authorized users can generate tender documents.
* **Clean and Intuitive Interface:** User-friendly web interface for easy file uploading and document generation.
* **Downloadable Output:** Generates a single PDF file that users can easily download and share.

## How to Use

1.  **Access the Application:** Go to the public URL provided by Railway after deployment (e.g., `your-app-name-random-hash.up.railway.app`).
2.  **Log In:** Enter the valid username (`crm`) and password (`Inst@2025`) on the login page.
3.  **Upload Files:**
    * **Master PDF File:** Upload the main PDF document that contains the core tender information.
    * **Lot Files:** Upload one or more files containing specific details for different lots. You can upload PDF files directly, or upload JPG, PNG, or DOCX files, which will be automatically converted to PDF.
4.  **Generate Tender Document:** Click the "Generate Tender Document" button.
5.  **Download:** Once the process is complete, a combined PDF file named `tender_generated.pdf` will be downloaded to your computer.
6.  **Logout:** Click the "Logout" button to securely end your session.

## Deployment

This application is designed to be easily deployed on [Railway](https://railway.app/).

### Prerequisites

* A Railway account.
* The application code hosted on a GitHub repository.

### Deployment Steps

1.  **Clone the Repository:** Clone your `TenderFlow` repository to your local machine.
2.  **Create a `Procfile`:** Ensure you have a `Procfile` in the root of your repository with the following content:
    ```
    web: uvicorn api.tender:app --host 0.0.0.0 --port $PORT
    ```
3.  **Create `requirements.txt`:** Make sure you have a `requirements.txt` file in the root of your repository listing the necessary Python dependencies:
    ```
    fastapi
    uvicorn[standard]
    pypandoc
    Pillow
    PyPDF2
    ```
4.  **Connect to Railway:**
    * Log in to your Railway account.
    * Create a new project and select "Deploy from GitHub Repo."
    * Authorize Railway to access your repository and select `TenderFlow`.
5.  **Configure Variables:**
    * Go to the "Variables" tab of your Railway application.
    * Add the following environment variables:
        * `VALID_USERNAME`: ``
        * `VALID_PASSWORD`: ``
6.  **Deploy:** Railway will automatically build and deploy your application. The public URL will be available in the "Networking" tab of your application service.

## Technologies Used

* [FastAPI](https://fastapi.tiangolo.com/): A modern, fast (high-performance), web framework for building APIs with Python.
* [Uvicorn](https://www.uvicorn.org/): An ASGI server for Python.
* [Pillow](https://pillow.readthedocs.io/en/stable/): Python Imaging Library for image processing.
* [PyPDF2](https://pypdf2.readthedocs.io/en/latest/): A pure-Python PDF library capable of splitting, merging, cropping, and transforming the pages of PDF files.
* [pypandoc](https://pypandoc.readthedocs.io/en/latest/): A thin wrapper around pandoc, a universal document converter, used for converting DOCX to PDF.
* [Railway](https://railway.app/): A modern platform to deploy web applications.

## Security

* Access to TenderFlow is protected by a simple username and password. **For production environments, it is highly recommended to implement more robust authentication and authorization mechanisms.**
* Sensitive information (username and password) should be managed as environment variables.

## Future Enhancements

* More sophisticated user management.
* Options for customizing the output PDF (e.g., adding headers, footers, watermarks).
* Support for more input file formats.
* Integration with cloud storage services.
