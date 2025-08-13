import os
import uuid
from werkzeug.utils import secure_filename
from PIL import Image
from flask import current_app

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def save_uploaded_file(file, folder='general'):
    """Save uploaded file and return filename"""
    if file and allowed_file(file.filename):
        # Generate unique filename
        filename = secure_filename(file.filename)
        name, ext = os.path.splitext(filename)
        unique_filename = f"{uuid.uuid4().hex}{ext}"
        
        # Create folder path
        upload_path = os.path.join(
            current_app.instance_path,
            current_app.config['UPLOAD_FOLDER'],
            folder
        )
        os.makedirs(upload_path, exist_ok=True)
        
        # Save file
        file_path = os.path.join(upload_path, unique_filename)
        file.save(file_path)
        
        # Resize image if it's too large
        try:
            with Image.open(file_path) as img:
                if img.width > 1200 or img.height > 1200:
                    img.thumbnail((1200, 1200), Image.Resampling.LANCZOS)
                    img.save(file_path, optimize=True, quality=85)
        except Exception:
            pass  # Not an image or couldn't process
        
        return f"{folder}/{unique_filename}"
    
    return None

def format_datetime(dt):
    """Format datetime for API response"""
    if dt:
        return dt.isoformat()
    return None

def paginate_query(query, page=1, per_page=20):
    """Paginate SQLAlchemy query"""
    return query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )