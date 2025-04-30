import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PyPDF2 import PdfMerger
from PIL import Image
import shutil
import os
import tempfile

class TenderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🧾 Tender Generator")
        self.root.geometry("600x600")
        self.root.resizable(False, False)

        self.new_folder_path = None
        self.master_file_path = None
        self.lot_folder_path = None

        self.setup_ui()

    def setup_ui(self):
        # Folder name input
        self.folder_name_label = ttk.Label(self.root, text="Enter Folder Name:")
        self.folder_name_label.pack(pady=10)

        self.folder_name_entry = ttk.Entry(self.root, font=('Arial', 12), width=30)
        self.folder_name_entry.pack(pady=5)

        ttk.Button(self.root, text="Create Folder", command=self.create_folder).pack(pady=10)

        # Master file upload section
        self.master_file_button = ttk.Button(self.root, text="Upload Master File", command=self.upload_master_file, state=tk.DISABLED)
        self.master_file_button.pack(pady=10)

        # Lot folder upload section
        self.lot_folder_button = ttk.Button(self.root, text="Upload Lot Folder (with documents)", command=self.upload_lot_folder, state=tk.DISABLED)
        self.lot_folder_button.pack(pady=10)

        # Generate Tender Button
        self.generate_button = ttk.Button(self.root, text="Generate Tender", command=self.generate_tender, state=tk.DISABLED)
        self.generate_button.pack(pady=10)

    def create_folder(self):
        folder_name = self.folder_name_entry.get()
        if not folder_name:
            messagebox.showerror("Input Error", "Please enter a folder name.")
            return

        folder_name = folder_name.strip()

        self.new_folder_path = os.path.join(os.getcwd(), folder_name)

        if os.path.exists(self.new_folder_path):
            messagebox.showerror("Folder Error", f"Folder '{folder_name}' already exists.")
            return

        try:
            os.makedirs(self.new_folder_path)
            messagebox.showinfo("Success", f"Folder '{folder_name}' created successfully!")
            self.master_file_button.config(state=tk.NORMAL)
        except Exception as e:
            messagebox.showerror("Folder Creation Error", f"Error creating folder:\n{e}")

    def upload_master_file(self):
        if not self.new_folder_path:
            messagebox.showerror("Folder Error", "Please create a folder first.")
            return

        master_file_path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if master_file_path:
            self.master_file_path = master_file_path
            try:
                destination_path = os.path.join(self.new_folder_path, os.path.basename(master_file_path))
                shutil.copy2(master_file_path, destination_path)
                messagebox.showinfo("Success", f"Master file uploaded successfully to {destination_path}")
                self.lot_folder_button.config(state=tk.NORMAL)
            except Exception as e:
                messagebox.showerror("File Copy Error", f"Error copying the master file:\n{e}")

    def upload_lot_folder(self):
        if not self.new_folder_path or not self.master_file_path:
            messagebox.showerror("Error", "Please upload the master file first.")
            return

        # Ask the user to upload a folder
        lot_folder_path = filedialog.askdirectory(title="Select Lot Folder (with documents)")
        if lot_folder_path:
            self.lot_folder_path = lot_folder_path

            # Check if the required files exist in the folder
            required_files = ['Bid Security.jpg', 'Cover Letter.pdf', 'DRAP.pdf', 'Technical Quotation.pdf']
            missing_files = []

            for file in required_files:
                if not os.path.exists(os.path.join(self.lot_folder_path, file)):
                    missing_files.append(file)

            if missing_files:
                messagebox.showerror("Missing Files", f"These files are missing in the folder:\n" + "\n".join(missing_files))
                return

            messagebox.showinfo("Success", f"Lot folder uploaded successfully.\nAll required files are present.")
            self.generate_button.config(state=tk.NORMAL)

    def convert_image_to_pdf(self, image_path):
        try:
            image = Image.open(image_path).convert("RGB")
            temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
            image.save(temp_pdf.name)
            return temp_pdf.name
        except Exception as e:
            messagebox.showerror("Image Conversion Error", f"Error converting image to PDF:\n{e}")
            return None

    def generate_tender(self):
        if not self.new_folder_path or not self.master_file_path or not self.lot_folder_path:
            messagebox.showerror("Input Error", "Please ensure all files and folders are uploaded correctly.")
            return

        master_file_in_new_folder = os.path.join(self.new_folder_path, os.path.basename(self.master_file_path))

        if not os.path.exists(master_file_in_new_folder):
            messagebox.showerror("Missing File", "Master file not found in the newly created folder.")
            return

        # Collect all required documents from the Lot folder
        tender_files = []
        lot_files = ['Bid Security.jpg', 'Cover Letter.pdf', 'DRAP.pdf', 'Technical Quotation.pdf']

        for file in lot_files:
            file_path = os.path.join(self.lot_folder_path, file)
            if os.path.exists(file_path):
                tender_files.append(file_path)
            else:
                messagebox.showerror("Missing File", f"The file {file} is missing in the Lot folder.")
                return

        # Merge PDFs from the documents folder and the master file
        try:
            merger = PdfMerger()

            # Append the master file
            merger.append(master_file_in_new_folder)

            # Append document files (Bid Security, Cover Letter, DRAP, Technical Quotation)
            for file in tender_files:
                if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                    pdf_path = self.convert_image_to_pdf(file)
                    if pdf_path:
                        merger.append(pdf_path)
                elif file.lower().endswith('.pdf'):
                    merger.append(file)
                else:
                    messagebox.showerror("Unsupported File", f"{file} must be a PDF or image file.")
                    return

            # Save the merged tender file
            tender_output_path = os.path.join(self.new_folder_path, f"Tender_{os.path.basename(self.lot_folder_path)}.pdf")
            merger.write(tender_output_path)
            merger.close()

            messagebox.showinfo("Success", f"Tender generated successfully: {tender_output_path}")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred:\n{e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = TenderApp(root)
    root.mainloop()
