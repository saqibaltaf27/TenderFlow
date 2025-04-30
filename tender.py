import tkinter as tk
from tkinter import filedialog, messagebox, ttk, simpledialog
from PyPDF2 import PdfMerger
from PIL import Image
import os
import shutil
import tempfile
import re

REQUIRED_FILES = ['Bid Security.jpg', 'Cover Letter.pdf', 'DRAP.pdf', 'Technical Quotation.pdf']


class TenderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🧾 Tender Generator")
        self.root.geometry("600x600")
        self.root.resizable(False, False)

        self.new_folder_path = None
        self.master_file_path = None
        self.lot_folder_path = None

        self.style = ttk.Style(self.root)
        self.configure_styles()
        self.setup_ui()

    def configure_styles(self):
        self.style.theme_use("clam")

        # Lighter Button Style
        self.style.configure("TButton",
                             foreground="black",
                             background="#4caf50",  # Light greenish color
                             font=("Segoe UI", 10, "bold"),
                             borderwidth=1,
                             focusthickness=3,
                             focuscolor='none',
                             padding=6)

        self.style.map("TButton",
                       background=[("active", "#45a049")],
                       relief=[("pressed", "sunken")])

        # Lighter Label Style
        self.style.configure("TLabel",
                             foreground="black",
                             background="#f0f0f0",  # Light grey background
                             font=("Segoe UI", 10))

        # Header Style for Title
        self.style.configure("Header.TLabel",
                             foreground="#007bff",  # Lighter blue
                             background="#f0f0f0",  # Light grey background
                             font=("Segoe UI", 20, "bold"))

    def setup_ui(self):
        ttk.Label(self.root, text="Tender Generator", style="Header.TLabel").pack(pady=20)

        ttk.Label(self.root, text="Create New Folder or Select Existing Folder:").pack(pady=10)

        ttk.Button(self.root, text="Create New Folder", command=self.create_folder).pack(pady=5)
        ttk.Button(self.root, text="Select Existing Folder", command=self.select_existing_folder).pack(pady=5)

        self.master_file_button = ttk.Button(self.root, text="Upload Master File", command=self.upload_master_file, state=tk.DISABLED)
        self.master_file_button.pack(pady=10)

        self.lot_folder_button = ttk.Button(self.root, text="Upload Lot Folder (with documents)", command=self.upload_lot_folder, state=tk.DISABLED)
        self.lot_folder_button.pack(pady=10)

        self.generate_button = ttk.Button(self.root, text="Generate Tender", command=self.generate_tender, state=tk.DISABLED)
        self.generate_button.pack(pady=10)

    def create_folder(self):
        folder_name = simpledialog.askstring("Folder Name", "Enter folder name:")
        if not folder_name or not folder_name.strip():
            messagebox.showerror("Input Error", "Please enter a valid folder name.")
            return

        folder_path = os.path.join(os.getcwd(), folder_name.strip())
        if os.path.exists(folder_path):
            messagebox.showerror("Folder Error", f"Folder '{folder_name}' already exists.")
            return

        try:
            os.makedirs(folder_path)
            self.new_folder_path = folder_path
            messagebox.showinfo("Success", f"Folder '{folder_name}' created successfully!")
            self.master_file_button.config(state=tk.NORMAL)
        except Exception as e:
            messagebox.showerror("Folder Creation Error", str(e))

    def select_existing_folder(self):
        folder = filedialog.askdirectory(title="Select Existing Folder")
        if not folder:
            return

        self.new_folder_path = folder
        if self.check_master_file_in_folder():
            messagebox.showinfo("Success", f"Selected existing folder: {folder}")
            self.lot_folder_button.config(state=tk.NORMAL)
        else:
            messagebox.showerror("Missing Master File", "Master PDF file not found in the selected folder.")

    def check_master_file_in_folder(self):
        for filename in os.listdir(self.new_folder_path):
            if "master" in filename.lower() and filename.lower().endswith(".pdf"):
                self.master_file_path = os.path.join(self.new_folder_path, filename)
                return True
        return False

    def upload_master_file(self):
        if not self.new_folder_path:
            messagebox.showerror("Folder Error", "Create or select a folder first.")
            return

        file_path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if not file_path:
            return

        try:
            dest_path = os.path.join(self.new_folder_path, os.path.basename(file_path))
            shutil.copy2(file_path, dest_path)
            self.master_file_path = dest_path
            messagebox.showinfo("Success", f"Master file uploaded to: {dest_path}")
            self.lot_folder_button.config(state=tk.NORMAL)
        except Exception as e:
            messagebox.showerror("Upload Error", str(e))

    def upload_lot_folder(self):
        if not self.master_file_path:
            messagebox.showerror("Missing File", "Upload the master file first.")
            return

        folder = filedialog.askdirectory(title="Select Lot Folder (with documents)")
        if not folder:
            return

        self.lot_folder_path = folder
        missing = [f for f in REQUIRED_FILES if not os.path.exists(os.path.join(folder, f))]

        if missing:
            messagebox.showerror("Missing Files", "These files are missing:\n" + "\n".join(missing))
            return

        messagebox.showinfo("Success", "All required Lot files are present.")
        self.generate_button.config(state=tk.NORMAL)

    def convert_image_to_pdf(self, image_path):
        try:
            image = Image.open(image_path).convert("RGB")
            temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
            image.save(temp_pdf.name)
            return temp_pdf.name
        except Exception as e:
            messagebox.showerror("Conversion Error", str(e))
            return None

    def generate_tender(self):
        if not all([self.new_folder_path, self.master_file_path, self.lot_folder_path]):
            messagebox.showerror("Missing Input", "Please upload all required files and folders.")
            return

        tender_files = []
        for file in REQUIRED_FILES:
            file_path = os.path.join(self.lot_folder_path, file)
            if not os.path.exists(file_path):
                messagebox.showerror("Missing File", f"{file} is missing.")
                return
            tender_files.append(file_path)

        try:
            merger = PdfMerger()
            merger.append(self.master_file_path)

            for file in tender_files:
                if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                    pdf_file = self.convert_image_to_pdf(file)
                    if pdf_file:
                        merger.append(pdf_file)
                elif file.lower().endswith('.pdf'):
                    merger.append(file)
                else:
                    messagebox.showerror("Invalid File", f"{file} is not a supported format.")
                    return

            output_path = os.path.join(self.new_folder_path, f"Tender_{os.path.basename(self.lot_folder_path)}.pdf")
            merger.write(output_path)
            merger.close()

            messagebox.showinfo("Success", f"Tender generated:\n{output_path}")
        except Exception as e:
            messagebox.showerror("Generation Error", str(e))


if __name__ == "__main__":
    root = tk.Tk()
    app = TenderApp(root)
    root.mainloop()
