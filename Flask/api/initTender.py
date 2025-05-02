import os
import subprocess
import webbrowser
import time

FASTAPI_APP = "tender.py"

subprocess.Popen(["uvicorn", "tender:app", "--host", "0.0.0.0", "--port", "8000"])

time.sleep(2)

webbrowser.open("http://localhost:8000")
