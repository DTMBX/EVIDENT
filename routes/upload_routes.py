"""
Evident Media Upload & Processing Routes
Handles batch and single file uploads with AI processing
"""

import os
import json
from pathlib import Path
from flask import (
    Blueprint, request, jsonify, render_template, 
    current_app, send_file, flash, redirect, url_for
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from datetime import datetime

# Import media processing service
from services.media_processor import (
    get_media_processor, 
    get_batch_processor,
    MediaValidator,
    ProcessingStatus
)

# Create blueprint
upload_bp = Blueprint('upload', __name__, url_prefix='/upload')


# ============================================================================
# UPLOAD CONFIGURATION
# ============================================================================

UPLOAD_DIR = 'uploads'
ALLOWED_EXTENSIONS = (
    # Video formats
    'mp4', 'avi', 'mov', 'mkv', 'webm', 'flv',
    # Audio formats
    'mp3', 'wav', 'flac', 'aac', 'wma', 'm4a',
    # Image formats
    'jpeg', 'jpg', 'png', 'gif', 'bmp', 'webp', 'tiff',
    # PDF
    'pdf',
    # Documents
    'docx', 'doc', 'xlsx', 'xls', 'pptx', 'ppt', 'txt', 'rtf'
)

MAX_FILE_SIZE = 500 * 1024 * 1024  # 500 MB


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def create_user_upload_dir(user_id: int) -> Path:
    """Create user-specific upload directory"""
    user_dir = Path(UPLOAD_DIR) / f"user_{user_id}" / datetime.utcnow().strftime("%Y%m%d")
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir


def save_upload_metadata(file_id: str, user_id: int, metadata: dict):
    """Save upload metadata to JSON"""
    metadata_dir = Path(UPLOAD_DIR) / f"user_{user_id}" / "metadata"
    metadata_dir.mkdir(parents=True, exist_ok=True)
    
    metadata_file = metadata_dir / f"{file_id}.json"
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)


def get_upload_metadata(file_id: str, user_id: int) -> dict:
    """Get upload metadata from JSON"""
    metadata_file = Path(UPLOAD_DIR) / f"user_{user_id}" / "metadata" / f"{file_id}.json"
    
    if metadata_file.exists():
        with open(metadata_file, 'r') as f:
            return json.load(f)
    
    return {}


# ============================================================================
# ROUTES: Single File Upload
# ============================================================================

@upload_bp.route('/single', methods=['GET', 'POST'])
@login_required
def upload_single():
    """Upload and process a single file"""
    
    if request.method == 'GET':
        return render_template('upload/single.html', user=current_user)
    
    # Handle POST request
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({
            'error': f'File type not allowed. Supported: {", ".join(ALLOWED_EXTENSIONS)}'
        }), 400
    
    # Check file size
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    
    if file_size > MAX_FILE_SIZE:
        return jsonify({
            'error': f'File too large. Max size: {MAX_FILE_SIZE / (1024*1024):.0f}MB'
        }), 400
    
    # Validate with media validator
    is_valid, error_msg = MediaValidator.validate_file(file.filename, file_size)
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    try:
        # Create user upload directory
        user_dir = create_user_upload_dir(current_user.id)
        
        # Secure filename and save
        filename = secure_filename(file.filename)
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_")
        saved_filename = timestamp + filename
        file_path = user_dir / saved_filename
        
        file.save(str(file_path))
        
        # Process the file
        processor = get_media_processor(UPLOAD_DIR)
        result = processor.process_file(str(file_path))
        
        # Save metadata
        result_dict = result.to_dict()
        result_dict['user_id'] = current_user.id
        result_dict['upload_path'] = str(file_path)
        
        save_upload_metadata(result.file_id, current_user.id, result_dict)
        
        return jsonify({
            'success': True,
            'file_id': result.file_id,
            'filename': result.filename,
            'media_type': result.media_type.value,
            'status': result.status.value,
            'file_size': result.file_size,
            'metadata': result.metadata,
            'processing_time': result.processing_time,
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Upload error: {e}", exc_info=True)
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500


# ============================================================================
# ROUTES: Batch Upload
# ============================================================================

@upload_bp.route('/batch', methods=['GET', 'POST'])
@login_required
def upload_batch():
    """Batch upload and process multiple files"""
    
    if request.method == 'GET':
        return render_template('upload/batch.html', user=current_user)
    
    # Handle POST request
    if 'files' not in request.files:
        return jsonify({'error': 'No files provided'}), 400
    
    files = request.files.getlist('files')
    
    if not files or len(files) == 0:
        return jsonify({'error': 'No files selected'}), 400
    
    if len(files) > 50:
        return jsonify({'error': 'Maximum 50 files per batch'}), 400
    
    try:
        # Create user upload directory
        user_dir = create_user_upload_dir(current_user.id)
        
        # Validate and save files
        saved_files = []
        errors = []
        
        for file in files:
            if file.filename == '':
                continue
            
            if not allowed_file(file.filename):
                errors.append(f"{file.filename}: File type not allowed")
                continue
            
            # Check file size
            file.seek(0, os.SEEK_END)
            file_size = file.tell()
            file.seek(0)
            
            if file_size > MAX_FILE_SIZE:
                errors.append(f"{file.filename}: File too large")
                continue
            
            # Validate with media validator
            is_valid, error_msg = MediaValidator.validate_file(file.filename, file_size)
            if not is_valid:
                errors.append(f"{file.filename}: {error_msg}")
                continue
            
            # Save file
            filename = secure_filename(file.filename)
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_")
            saved_filename = timestamp + filename
            file_path = user_dir / saved_filename
            
            file.save(str(file_path))
            saved_files.append(str(file_path))
        
        if not saved_files:
            return jsonify({
                'error': 'No files could be saved',
                'details': errors
            }), 400
        
        # Process batch
        batch_processor = get_batch_processor(UPLOAD_DIR)
        batch_result = batch_processor.process_batch(saved_files)
        
        # Save batch metadata
        batch_metadata = {
            'batch_id': f"batch_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            'user_id': current_user.id,
            'timestamp': datetime.utcnow().isoformat(),
            'file_count': len(saved_files),
            'errors': errors,
            'results': batch_result['results'],
        }
        
        user_batch_dir = Path(UPLOAD_DIR) / f"user_{current_user.id}" / "batches"
        user_batch_dir.mkdir(parents=True, exist_ok=True)
        
        batch_file = user_batch_dir / f"batch_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        with open(batch_file, 'w') as f:
            json.dump(batch_metadata, f, indent=2)
        
        return jsonify({
            'success': True,
            'batch_summary': batch_processor.get_summary(),
            'results': batch_result['results'],
            'errors': errors,
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Batch upload error: {e}", exc_info=True)
        return jsonify({'error': f'Batch upload failed: {str(e)}'}), 500


# ============================================================================
# ROUTES: Upload Management
# ============================================================================

@upload_bp.route('/history', methods=['GET'])
@login_required
def upload_history():
    """Get user's upload history"""
    
    batch_dir = Path(UPLOAD_DIR) / f"user_{current_user.id}" / "batches"
    
    if not batch_dir.exists():
        return render_template('upload/history.html', 
                             user=current_user,
                             batches=[])
    
    # Load all batch metadata files
    batches = []
    for batch_file in sorted(batch_dir.glob('*.json'), reverse=True)[:20]:  # Last 20
        try:
            with open(batch_file, 'r') as f:
                batch_data = json.load(f)
                batches.append(batch_data)
        except Exception as e:
            current_app.logger.error(f"Error reading batch file {batch_file}: {e}")
    
    return render_template('upload/history.html', 
                         user=current_user,
                         batches=batches)


@upload_bp.route('/api/detail/<file_id>', methods=['GET'])
@login_required
def get_upload_detail(file_id: str):
    """Get detailed information about an upload"""
    
    try:
        metadata = get_upload_metadata(file_id, current_user.id)
        
        if not metadata:
            return jsonify({'error': 'Upload not found'}), 404
        
        return jsonify(metadata), 200
        
    except Exception as e:
        current_app.logger.error(f"Error getting upload detail: {e}")
        return jsonify({'error': 'Failed to retrieve details'}), 500


@upload_bp.route('/api/status/<file_id>', methods=['GET'])
@login_required
def get_upload_status(file_id: str):
    """Get processing status of an upload"""
    
    try:
        metadata = get_upload_metadata(file_id, current_user.id)
        
        if not metadata:
            return jsonify({'error': 'Upload not found'}), 404
        
        return jsonify({
            'file_id': file_id,
            'status': metadata.get('status', 'unknown'),
            'processing_time': metadata.get('processing_time', 0),
            'filename': metadata.get('filename'),
            'media_type': metadata.get('media_type'),
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error getting upload status: {e}")
        return jsonify({'error': 'Failed to get status'}), 500


@upload_bp.route('/api/delete/<file_id>', methods=['DELETE'])
@login_required
def delete_upload(file_id: str):
    """Delete an uploaded file"""
    
    try:
        metadata = get_upload_metadata(file_id, current_user.id)
        
        if not metadata:
            return jsonify({'error': 'Upload not found'}), 404
        
        # Delete the file
        file_path = Path(metadata.get('upload_path', ''))
        if file_path.exists():
            file_path.unlink()
        
        # Delete metadata
        metadata_file = Path(UPLOAD_DIR) / f"user_{current_user.id}" / "metadata" / f"{file_id}.json"
        if metadata_file.exists():
            metadata_file.unlink()
        
        return jsonify({'success': True}), 200
        
    except Exception as e:
        current_app.logger.error(f"Error deleting upload: {e}")
        return jsonify({'error': 'Failed to delete'}), 500


# ============================================================================
# ROUTES: Status & Statistics
# ============================================================================

@upload_bp.route('/api/stats', methods=['GET'])
@login_required
def get_upload_stats():
    """Get upload statistics for current user"""
    
    try:
        metadata_dir = Path(UPLOAD_DIR) / f"user_{current_user.id}" / "metadata"
        batch_dir = Path(UPLOAD_DIR) / f"user_{current_user.id}" / "batches"
        
        # Count uploads
        upload_count = len(list(metadata_dir.glob('*.json'))) if metadata_dir.exists() else 0
        batch_count = len(list(batch_dir.glob('*.json'))) if batch_dir.exists() else 0
        
        # Calculate total size
        user_dir = Path(UPLOAD_DIR) / f"user_{current_user.id}"
        total_size = sum(f.stat().st_size for f in user_dir.rglob('*') if f.is_file())
        
        return jsonify({
            'total_uploads': upload_count,
            'total_batches': batch_count,
            'total_size_mb': total_size / (1024 * 1024),
            'quota_mb': 1000,  # Example: 1GB quota
            'quota_usage_percent': (total_size / (1024 * 1024)) / 1000 * 100,
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error getting upload stats: {e}")
        return jsonify({'error': 'Failed to get statistics'}), 500
