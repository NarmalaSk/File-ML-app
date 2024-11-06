import os
import pytesseract
from PIL import Image
import shutil
from flask import Flask, request, render_template, redirect, url_for, flash, send_from_directory
from werkzeug.utils import secure_filename
import zipfile
import tempfile

# Set up Flask app
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'organized_images'
app.config['SECRET_KEY'] = 'your_secret_key'  # Change this to a random secret key

# Keywords to categorize images
KEYWORDS = ["invoice", "report", "contract", "receipt", "letter"]

# Ensure necessary directories
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

def organize_images():
    # Organize images based on detected text
    for filename in os.listdir(app.config['UPLOAD_FOLDER']):
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            try:
                img = Image.open(image_path)
                text = pytesseract.image_to_string(img).lower()

                matched = False
                for keyword in KEYWORDS:
                    if keyword in text:
                        keyword_folder = os.path.join(app.config['OUTPUT_FOLDER'], keyword)
                        os.makedirs(keyword_folder, exist_ok=True)
                        shutil.move(image_path, os.path.join(keyword_folder, filename))
                        matched = True
                        break

                if not matched:
                    uncategorized_folder = os.path.join(app.config['OUTPUT_FOLDER'], "Uncategorized")
                    os.makedirs(uncategorized_folder, exist_ok=True)
                    shutil.move(image_path, os.path.join(uncategorized_folder, filename))
            except Exception as e:
                print(f"Error processing {filename}: {e}")

def zip_directory(directory_path, zip_name):
    """Compress a directory into a zip file."""
    zip_path = os.path.join(directory_path, f"{zip_name}.zip")
    shutil.make_archive(zip_path.replace('.zip', ''), 'zip', directory_path)
    return zip_path

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if "upload_folder" in request.files:
            uploaded_file = request.files["upload_folder"]
            if uploaded_file.filename.endswith('.zip'):
                zip_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(uploaded_file.filename))
                uploaded_file.save(zip_path)

                # Extract ZIP contents to upload folder
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(app.config['UPLOAD_FOLDER'])

                flash("Images uploaded successfully. Click submit to organize them.", "success")
                os.remove(zip_path)
            else:
                flash("Please upload a .zip file containing images.", "danger")

        elif "upload_directory" in request.files:
            uploaded_folder = request.files["upload_directory"]
            if uploaded_folder and uploaded_folder.filename:
                folder_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(uploaded_folder.filename))
                uploaded_folder.save(folder_path)

                flash("Folder uploaded successfully. Click submit to organize them.", "success")

        elif request.form.get("submit"):
            organize_images()
            flash("Images have been organized based on detected keywords.", "success")

            # After organizing, create a ZIP file of the organized folder
            organized_folder_zip = zip_directory(app.config['OUTPUT_FOLDER'], "organized_images")
            return send_from_directory(
                directory=os.getcwd(),
                filename=organized_folder_zip,
                as_attachment=True
            )

    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
