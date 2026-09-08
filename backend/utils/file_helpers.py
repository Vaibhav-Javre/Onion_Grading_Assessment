import os
import uuid
from werkzeug.utils import secure_filename
from config import Config

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in Config.ALLOWED_EXTENSIONS

def save_upload_file(file, destination_folder):
    """
    Saves an uploaded FileStorage object securely with a UUID prefix.
    Returns: (unique_filename, full_absolute_path)
    """
    os.makedirs(destination_folder, exist_ok=True)
    original_name = secure_filename(file.filename) or "upload.jpg"
    ext = original_name.rsplit(".", 1)[1].lower() if "." in original_name else "jpg"
    unique_filename = f"{uuid.uuid4().hex}_{original_name}"
    full_path = os.path.join(destination_folder, unique_filename)
    file.save(full_path)
    return unique_filename, full_path

def get_file_size_bytes(filepath):
    if os.path.exists(filepath):
        return os.path.getsize(filepath)
    return 0
