from flask import Blueprint, request, jsonify, current_app, send_from_directory
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from utils.helpers import allowed_file
import os
import uuid
from PIL import Image
import io

upload_bp = Blueprint('upload', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
MAX_IMAGE_SIZE = (1200, 1200)  # Max dimensions

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def resize_image(image_data, max_size=MAX_IMAGE_SIZE):
    """Resize image if it's too large"""
    try:
        image = Image.open(io.BytesIO(image_data))
        
        # Convert RGBA to RGB if necessary
        if image.mode == 'RGBA':
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[-1])
            image = background
        
        # Resize if necessary
        if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
            image.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Save to bytes
        output = io.BytesIO()
        image.save(output, format='JPEG', quality=85, optimize=True)
        return output.getvalue()
    except Exception as e:
        raise ValueError(f"Error processing image: {str(e)}")

@upload_bp.route('/upload/avatar', methods=['POST'])
@jwt_required()
def upload_avatar():
    """Upload user avatar"""
    try:
        current_user_id = get_jwt_identity()
        
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed. Please use PNG, JPG, JPEG, GIF, or WEBP'}), 400
        
        # Check file size
        file_data = file.read()
        if len(file_data) > MAX_FILE_SIZE:
            return jsonify({'error': 'File size too large. Maximum size is 5MB'}), 400
        
        # Reset file pointer
        file.seek(0)
        
        # Resize image
        try:
            resized_data = resize_image(file_data)
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        
        # Generate unique filename
        file_extension = file.filename.rsplit('.', 1)[1].lower()
        filename = f"avatar_{current_user_id}_{uuid.uuid4().hex}.jpg"
        
        # Ensure upload directory exists
        upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'avatars')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save file
        file_path = os.path.join(upload_dir, filename)
        with open(file_path, 'wb') as f:
            f.write(resized_data)
        
        # Generate URL
        file_url = f"/uploads/avatars/{filename}"
        
        return jsonify({
            'message': 'Avatar uploaded successfully',
            'file_url': file_url,
            'filename': filename
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@upload_bp.route('/upload/event-image', methods=['POST'])
@jwt_required()
def upload_event_image():
    """Upload event image"""
    try:
        current_user_id = get_jwt_identity()
        
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed. Please use PNG, JPG, JPEG, GIF, or WEBP'}), 400
        
        # Check file size
        file_data = file.read()
        if len(file_data) > MAX_FILE_SIZE:
            return jsonify({'error': 'File size too large. Maximum size is 5MB'}), 400
        
        # Reset file pointer
        file.seek(0)
        
        # Resize image
        try:
            resized_data = resize_image(file_data)
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        
        # Generate unique filename
        file_extension = file.filename.rsplit('.', 1)[1].lower()
        filename = f"event_{current_user_id}_{uuid.uuid4().hex}.jpg"
        
        # Ensure upload directory exists
        upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'events')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save file
        file_path = os.path.join(upload_dir, filename)
        with open(file_path, 'wb') as f:
            f.write(resized_data)
        
        # Generate URL
        file_url = f"/uploads/events/{filename}"
        
        return jsonify({
            'message': 'Event image uploaded successfully',
            'file_url': file_url,
            'filename': filename
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@upload_bp.route('/uploads/<path:filename>', methods=['GET'])
def serve_uploaded_file(filename):
    """Serve uploaded files"""
    try:
        upload_dir = current_app.config['UPLOAD_FOLDER']
        return send_from_directory(upload_dir, filename)
    except Exception as e:
        return jsonify({'error': 'File not found'}), 404

@upload_bp.route('/upload/delete', methods=['DELETE'])
@jwt_required()
def delete_uploaded_file():
    """Delete an uploaded file"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        filename = data.get('filename')
        
        if not filename:
            return jsonify({'error': 'Filename is required'}), 400
        
        # Security check: ensure filename belongs to current user
        if not (filename.startswith(f'avatar_{current_user_id}_') or 
                filename.startswith(f'event_{current_user_id}_')):
            return jsonify({'error': 'Unauthorized to delete this file'}), 403
        
        # Determine file path
        if filename.startswith('avatar_'):
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'avatars', filename)
        elif filename.startswith('event_'):
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'events', filename)
        else:
            return jsonify({'error': 'Invalid filename format'}), 400
        
        # Delete file if it exists
        if os.path.exists(file_path):
            os.remove(file_path)
            return jsonify({'message': 'File deleted successfully'}), 200
        else:
            return jsonify({'error': 'File not found'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@upload_bp.route('/upload/info', methods=['GET'])
def get_upload_info():
    """Get upload configuration info"""
    return jsonify({
        'max_file_size': MAX_FILE_SIZE,
        'max_file_size_mb': MAX_FILE_SIZE // (1024 * 1024),
        'allowed_extensions': list(ALLOWED_EXTENSIONS),
        'max_image_dimensions': MAX_IMAGE_SIZE
    }), 200