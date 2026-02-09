"""
Optimized Upload Routes with Celery-based Async Processing
- Parallel batch processing for multiple videos
- Real-time progress tracking via WebSocket
- Multi-BWC synchronization
- Streaming transcription results
"""

import os
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import json
import uuid
from functools import wraps

from flask import Blueprint, request, jsonify, send_file
from flask_cors import cross_origin
from werkzeug.utils import secure_filename

from services.advanced_video_processor import (
    FFmpegVideoProcessor,
    BatchVideoProcessor,
    BWCSynchronizer,
    VideoQuality,
)
from auth.auth_required import auth_required, get_current_user
from models.database import db, MediaFile, ProcessingJob, Transcription

logger = logging.getLogger(__name__)

# Blueprint
upload_bp = Blueprint('upload', __name__, url_prefix='/api/upload')

# Configuration
UPLOAD_DIR = Path(os.getenv('UPLOAD_DIR', 'uploads'))
PROCESSED_DIR = Path(os.getenv('PROCESSED_DIR', 'processed'))
MAX_FILE_SIZE = 5 * 1024 * 1024 * 1024  # 5GB
ALLOWED_EXTENSIONS = {'.mp4', '.mov', '.avi', '.mkv', '.webm', '.flv', '.m4v'}
MAX_BATCH_SIZE = 50


# ======================== HELPERS ========================

def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed"""
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS


def secure_save_file(file, user_id: str, case_id: str) -> Optional[str]:
    """
    Securely save uploaded file
    Organization: uploads/user_{id}/case_{case_id}/{YYYYMMDD}/{filename}
    """
    if not file or file.filename == '':
        return None
    
    if not allowed_file(file.filename):
        raise ValueError(f"File type not allowed: {file.filename}")
    
    # Create directory structure
    date_dir = datetime.now().strftime('%Y%m%d')
    save_dir = UPLOAD_DIR / f'user_{user_id}' / f'case_{case_id}' / date_dir
    save_dir.mkdir(parents=True, exist_ok=True)
    
    # Secure filename
    filename = secure_filename(file.filename)
    file_id = str(uuid.uuid4())
    filename = f"{file_id}_{filename}"
    
    filepath = save_dir / filename
    file.save(str(filepath))
    
    if filepath.stat().st_size > MAX_FILE_SIZE:
        filepath.unlink()
        raise ValueError(f"File exceeds maximum size: {MAX_FILE_SIZE}")
    
    return str(filepath)


# ======================== SINGLE FILE UPLOAD ========================

@upload_bp.route('/single', methods=['POST'])
@cross_origin()
@auth_required
def upload_single_file():
    """
    Upload and process single video file
    
    Returns: {
        "file_id": "uuid",
        "filename": "video.mp4",
        "case_id": "case_123",
        "status": "processing",
        "task_id": "celery_task_id",
        "metadata": {...}
    }
    """
    try:
        # Validate request
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        case_id = request.form.get('case_id')
        extract_transcription = request.form.get('transcription', 'true').lower() == 'true'
        quality = request.form.get('quality', 'high')
        
        if not case_id:
            return jsonify({'error': 'case_id required'}), 400
        
        user_id = get_current_user()['id']
        
        # Save file
        filepath = secure_save_file(file, user_id, case_id)
        file_id = str(uuid.uuid4())
        
        # Extract metadata immediately
        metadata = FFmpegVideoProcessor.get_video_metadata(filepath)
        
        # Create DB records
        media_file = MediaFile(
            id=file_id,
            user_id=user_id,
            case_id=case_id,
            filename=file.filename,
            filepath=filepath,
            file_size=metadata.file_size,
            duration=metadata.duration,
            resolution=f"{metadata.resolution[0]}x{metadata.resolution[1]}",
            fps=metadata.fps,
            media_type='video',
        )
        db.session.add(media_file)
        db.session.commit()
        
        # Start async processing
        target_quality = VideoQuality(quality.lower())
        task_result = BatchVideoProcessor.process_video_file.delay(
            file_id=file_id,
            input_file=filepath,
            case_id=case_id,
            extract_transcription=extract_transcription,
            target_quality=target_quality,
        )
        
        job = ProcessingJob(
            id=str(uuid.uuid4()),
            user_id=user_id,
            case_id=case_id,
            media_file_id=file_id,
            task_type='video_processing',
            celery_task_id=task_result.id,
            status='queued',
            metadata={
                'filename': file.filename,
                'quality': quality,
                'transcription': extract_transcription,
            },
        )
        db.session.add(job)
        db.session.commit()
        
        return jsonify({
            'file_id': file_id,
            'filename': file.filename,
            'case_id': case_id,
            'status': 'queued',
            'task_id': task_result.id,
            'metadata': {
                'duration': metadata.duration,
                'fps': metadata.fps,
                'resolution': f"{metadata.resolution[0]}x{metadata.resolution[1]}",
                'file_size': metadata.file_size,
                'codec_video': metadata.codec_video,
                'codec_audio': metadata.codec_audio,
            },
            'queue_position': 'pending',  # Can be enhanced with actual queue depth
        }), 202
    
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        return jsonify({'error': 'Internal server error'}), 500


# ======================== BATCH UPLOAD (ULTRA-FAST) ========================

@upload_bp.route('/batch', methods=['POST'])
@cross_origin()
@auth_required
def upload_batch_files():
    """
    Upload and process multiple video files in PARALLEL
    
    Request: multipart/form-data with multiple files
    Query params:
        - case_id: Case identifier (required)
        - quality: high/medium/low (default: high)
        - transcription: true/false (default: true)
        - sync_bwc: true/false - Auto-sync multiple BWCs (default: true)
    
    Returns: {
        "batch_id": "batch_uuid",
        "case_id": "case_123",
        "status": "processing",
        "total_files": 5,
        "files": [
            {
                "file_id": "file_uuid",
                "filename": "bwc_01.mp4",
                "status": "queued",
                "task_id": "celery_task_id"
            }
        ],
        "ws_endpoint": "/ws/batch/batch_uuid"
    }
    """
    try:
        # Validate
        files = request.files.getlist('files')
        case_id = request.form.get('case_id') or request.args.get('case_id')
        
        if not case_id:
            return jsonify({'error': 'case_id required'}), 400
        
        if not files or len(files) == 0:
            return jsonify({'error': 'No files provided'}), 400
        
        if len(files) > MAX_BATCH_SIZE:
            return jsonify({
                'error': f'Too many files. Maximum is {MAX_BATCH_SIZE}'
            }), 400
        
        user_id = get_current_user()['id']
        extract_transcription = request.form.get('transcription', 'true').lower() == 'true'
        quality = request.form.get('quality', 'high')
        sync_bwc = request.form.get('sync_bwc', 'true').lower() == 'true'
        
        batch_id = str(uuid.uuid4())
        file_results = []
        file_list_for_processing = []
        
        # Save all files first
        for file in files:
            if not allowed_file(file.filename):
                logger.warning(f"Skipping file: {file.filename}")
                continue
            
            try:
                filepath = secure_save_file(file, user_id, case_id)
                file_id = str(uuid.uuid4())
                
                # Get metadata
                metadata = FFmpegVideoProcessor.get_video_metadata(filepath)
                
                # Create DB record
                media_file = MediaFile(
                    id=file_id,
                    user_id=user_id,
                    case_id=case_id,
                    filename=file.filename,
                    filepath=filepath,
                    file_size=metadata.file_size,
                    duration=metadata.duration,
                    resolution=f"{metadata.resolution[0]}x{metadata.resolution[1]}",
                    fps=metadata.fps,
                    media_type='video',
                    batch_id=batch_id,
                )
                db.session.add(media_file)
                db.session.flush()
                
                file_results.append({
                    'file_id': file_id,
                    'filename': file.filename,
                    'status': 'saved',
                    'metadata': {
                        'duration': metadata.duration,
                        'resolution': f"{metadata.resolution[0]}x{metadata.resolution[1]}",
                        'file_size': metadata.file_size,
                    },
                })
                
                file_list_for_processing.append((file_id, filepath, case_id))
            
            except Exception as e:
                logger.error(f"Error processing file {file.filename}: {e}")
                file_results.append({
                    'filename': file.filename,
                    'status': 'error',
                    'error': str(e),
                })
        
        db.session.commit()
        
        # Start batch processing
        target_quality = VideoQuality(quality.lower())
        batch_result = BatchVideoProcessor.process_batch(
            file_list=file_list_for_processing,
            extract_transcription=extract_transcription,
            target_quality=target_quality,
        )
        
        # Create batch job record
        job = ProcessingJob(
            id=str(uuid.uuid4()),
            user_id=user_id,
            case_id=case_id,
            task_type='batch_video_processing',
            celery_task_id=batch_result['batch_id'],
            status='queued',
            metadata={
                'batch_id': batch_id,
                'total_files': len(file_list_for_processing),
                'quality': quality,
                'transcription': extract_transcription,
                'sync_bwc': sync_bwc,
            },
        )
        db.session.add(job)
        db.session.commit()
        
        # Add task IDs to file results
        for result in file_results:
            if result['status'] == 'saved':
                result['task_id'] = batch_result['batch_id']
                result['status'] = 'queued'
        
        if sync_bwc and len(file_list_for_processing) > 1:
            # Trigger BWC synchronization
            video_streams = {
                str(i): filepath
                for i, (file_id, filepath, _) in enumerate(file_list_for_processing)
            }
            synchronizer = BWCSynchronizer()
            sync_points = synchronizer.find_sync_points(video_streams)
            
            logger.info(f"Found {len(sync_points)} sync points for batch {batch_id}")
        
        return jsonify({
            'batch_id': batch_id,
            'case_id': case_id,
            'status': 'processing',
            'total_files': len(file_list_for_processing),
            'submitted_files': len(file_results),
            'files': file_results,
            'processing_info': {
                'quality': quality,
                'transcription': extract_transcription,
                'bwc_sync': sync_bwc,
            },
            'ws_endpoint': f'/ws/batch/{batch_id}',
            'status_endpoint': f'/api/upload/batch/{batch_id}/status',
        }), 202
    
    except Exception as e:
        logger.error(f"Error in batch upload: {e}")
        return jsonify({'error': 'Internal server error'}), 500


# ======================== BATCH STATUS ========================

@upload_bp.route('/batch/<batch_id>/status', methods=['GET'])
@cross_origin()
@auth_required
def get_batch_status(batch_id: str):
    """Get current status of batch processing"""
    try:
        status = BatchVideoProcessor.get_batch_status(batch_id)
        return jsonify(status), 200
    except Exception as e:
        logger.error(f"Error getting batch status: {e}")
        return jsonify({'error': 'Internal server error'}), 500


# ======================== FILE STATUS ========================

@upload_bp.route('/file/<file_id>/status', methods=['GET'])
@cross_origin()
@auth_required
def get_file_status(file_id: str):
    """Get processing status of individual file"""
    try:
        media_file = MediaFile.query.get(file_id)
        if not media_file:
            return jsonify({'error': 'File not found'}), 404
        
        user_id = get_current_user()['id']
        if media_file.user_id != user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Get job info
        job = ProcessingJob.query.filter_by(media_file_id=file_id).first()
        
        if job and job.celery_task_id:
            from services.advanced_video_processor import celery_app
            from celery.result import AsyncResult
            
            task_result = AsyncResult(job.celery_task_id, app=celery_app)
            
            return jsonify({
                'file_id': file_id,
                'filename': media_file.filename,
                'status': task_result.status,
                'progress': task_result.info if task_result.state == 'PROGRESS' else None,
                'result': task_result.get() if task_result.ready() else None,
            }), 200
        
        return jsonify({
            'file_id': file_id,
            'filename': media_file.filename,
            'status': media_file.status or 'pending',
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting file status: {e}")
        return jsonify({'error': 'Internal server error'}), 500


# ======================== TRANSCRIPTION FETCH ========================

@upload_bp.route('/file/<file_id>/transcription', methods=['GET'])
@cross_origin()
@auth_required
def get_transcription(file_id: str):
    """Get transcription for processed video"""
    try:
        media_file = MediaFile.query.get(file_id)
        if not media_file:
            return jsonify({'error': 'File not found'}), 404
        
        user_id = get_current_user()['id']
        if media_file.user_id != user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        transcription = Transcription.query.filter_by(
            media_file_id=file_id
        ).first()
        
        if not transcription:
            return jsonify({'error': 'Transcription not available'}), 404
        
        return jsonify({
            'file_id': file_id,
            'full_text': transcription.full_text,
            'segments': json.loads(transcription.segments_json)
                if transcription.segments_json else [],
            'language': transcription.language,
            'created_at': transcription.created_at.isoformat(),
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting transcription: {e}")
        return jsonify({'error': 'Internal server error'}), 500


# ======================== QUALITY OPTIONS ========================

@upload_bp.route('/quality-options', methods=['GET'])
def get_quality_options():
    """List available transcoding quality options"""
    return jsonify({
        'qualities': [
            {
                'id': 'ultra_low',
                'name': 'Ultra Low (240p)',
                'description': 'Fastest, smallest file',
                'use_case': 'Preview, streaming on poor connection',
            },
            {
                'id': 'low',
                'name': 'Low (480p)',
                'description': 'Fast, mobile-friendly',
                'use_case': 'Mobile devices',
            },
            {
                'id': 'medium',
                'name': 'Medium (720p)',
                'description': 'Balanced speed and quality',
                'use_case': 'General purpose, streaming',
            },
            {
                'id': 'high',
                'name': 'High (1080p)',
                'description': 'High quality, slower processing',
                'use_case': 'Evidence documentation',
            },
            {
                'id': 'ultra_high',
                'name': 'Ultra High (4K)',
                'description': 'Best quality, slowest processing',
                'use_case': 'Archival, detailed analysis',
            },
        ]
    }), 200
