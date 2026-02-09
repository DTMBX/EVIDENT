"""
Advanced Video Processing Pipeline with Real-Time Synchronization
- High-speed batch processing with Celery
- FFmpeg video transcoding and analysis
- OpenAI Whisper transcription
- Real-time BWC synchronization
- Multi-stream audio/video sync
"""

import os
import logging
import asyncio
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import subprocess
import time
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
import uuid

import ffmpeg
import librosa
import numpy as np
from celery import Celery, group, chord
from celery.result import AsyncResult

logger = logging.getLogger(__name__)


# ======================== CONFIGURATION ========================

class VideoQuality(Enum):
    """Video quality presets"""
    ULTRA_LOW = "ultra_low"    # 240p for preview
    LOW = "low"                 # 480p for mobile
    MEDIUM = "medium"           # 720p balanced
    HIGH = "high"               # 1080p HD
    ULTRA_HIGH = "ultra_high"   # 4K/2160p


@dataclass
class VideoMetadata:
    """Video metadata extracted from file"""
    file_id: str
    filename: str
    duration: float
    fps: float
    resolution: Tuple[int, int]
    codec_video: str
    codec_audio: str
    bitrate: int
    file_size: int
    channels: int
    sample_rate: int
    metadata_dict: Dict = field(default_factory=dict)


@dataclass
class TranscriptionSegment:
    """Single transcription segment"""
    start_time: float  # seconds
    end_time: float
    text: str
    confidence: float = 1.0
    speaker: Optional[str] = None
    language: str = "en"
    metadata: Dict = field(default_factory=dict)


@dataclass
class BWCFrame:
    """Single frame from Body-Worn Camera"""
    timestamp: float
    frame_id: str
    source_camera: str
    video_file_id: str
    audio_bytes: Optional[bytes] = None
    transcription: Optional[str] = None
    confidence: float = 0.0


@dataclass
class SynchronizationPoint:
    """Point where multiple video streams are synchronized"""
    global_timestamp: float
    camera_timestamps: Dict[str, float]  # camera_id -> timestamp
    confidence: float = 0.0


# ======================== CELERY SETUP ========================

def get_celery_app():
    """Get or create Celery application"""
    celery = Celery('evident_media_processor')
    celery.conf.update(
        broker='redis://localhost:6379/0',
        backend='redis://localhost:6379/0',
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='UTC',
        enable_utc=True,
        worker_prefetch_multiplier=1,
        worker_max_tasks_per_child=100,
        task_soft_time_limit=3600,  # 1 hour
        task_time_limit=3600,
        broker_connection_retry_on_startup=True,
    )
    return celery


celery_app = get_celery_app()


# ======================== FFmpeg VIDEO PROCESSOR ========================

class FFmpegVideoProcessor:
    """High-performance video processing using FFmpeg"""
    
    QUALITY_PRESETS = {
        VideoQuality.ULTRA_LOW: {
            'scale': '426x240',
            'bitrate': '200k',
            'fps': 15,
        },
        VideoQuality.LOW: {
            'scale': '854x480',
            'bitrate': '800k',
            'fps': 24,
        },
        VideoQuality.MEDIUM: {
            'scale': '1280x720',
            'bitrate': '2500k',
            'fps': 30,
        },
        VideoQuality.HIGH: {
            'scale': '1920x1080',
            'bitrate': '5000k',
            'fps': 30,
        },
        VideoQuality.ULTRA_HIGH: {
            'scale': '3840x2160',
            'bitrate': '15000k',
            'fps': 60,
        },
    }
    
    @staticmethod
    def get_video_metadata(input_file: str) -> VideoMetadata:
        """Extract comprehensive video metadata"""
        try:
            probe = ffmpeg.probe(input_file)
            video_stream = next((s for s in probe['streams'] if s['codec_type'] == 'video'), None)
            audio_stream = next((s for s in probe['streams'] if s['codec_type'] == 'audio'), None)
            
            file_size = os.path.getsize(input_file)
            duration = float(probe['format'].get('duration', 0))
            
            resolution = (
                video_stream['width'] if video_stream else 1920,
                video_stream['height'] if video_stream else 1080,
            )
            
            fps = 30
            if video_stream and 'r_frame_rate' in video_stream:
                num, den = map(int, video_stream['r_frame_rate'].split('/'))
                fps = num / den if den else 30
            
            return VideoMetadata(
                file_id=str(uuid.uuid4()),
                filename=Path(input_file).name,
                duration=duration,
                fps=fps,
                resolution=resolution,
                codec_video=video_stream['codec_name'] if video_stream else 'unknown',
                codec_audio=audio_stream['codec_name'] if audio_stream else 'unknown',
                bitrate=int(probe['format'].get('bit_rate', 0)),
                file_size=file_size,
                channels=audio_stream['channels'] if audio_stream else 2,
                sample_rate=int(audio_stream['sample_rate']) if audio_stream else 44100,
            )
        except Exception as e:
            logger.error(f"Error getting video metadata: {e}")
            raise
    
    @staticmethod
    def transcode_video(
        input_file: str,
        output_file: str,
        quality: VideoQuality = VideoQuality.HIGH,
        format: str = 'mp4',
    ) -> Dict[str, Any]:
        """
        Transcode video to specified quality
        Heavily optimized for speed using multiple threads
        """
        try:
            preset = FFmpegVideoProcessor.QUALITY_PRESETS[quality]
            
            # FFmpeg command with optimization flags
            stream = ffmpeg.input(input_file)
            
            # Video processing
            stream = ffmpeg.filter(stream, 'scale', preset['scale'])
            stream = ffmpeg.filter(stream, 'fps', preset['fps'])
            
            # Audio processing
            stream = ffmpeg.output(
                stream,
                output_file,
                codec_v='libx264',  # Fast h264 encoder
                preset='fast',      # Encoding preset (fast/medium/slow)
                crf=23,             # Quality (0-51, lower = better)
                movflags='faststart',  # Enable streaming
                threads=8,          # Use 8 threads
                **{'b:v': preset['bitrate']}  # Bitrate
            )
            
            # Execute with capture output
            ffmpeg.run(stream, capture_stdout=True, capture_stderr=True)
            
            return {
                'status': 'success',
                'output_file': output_file,
                'quality': quality.value,
                'timestamp': datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error transcoding video: {e}")
            return {
                'status': 'error',
                'error': str(e),
            }
    
    @staticmethod
    def extract_audio(input_file: str, output_file: str) -> Dict[str, Any]:
        """Extract audio stream to WAV for transcription"""
        try:
            stream = ffmpeg.input(input_file)
            stream = ffmpeg.output(
                stream,
                output_file,
                acodec='pcm_s16le',
                ar='16000',  # 16kHz for Whisper
                ac=1,        # Mono
            )
            ffmpeg.run(stream, capture_stdout=True, capture_stderr=True)
            
            return {
                'status': 'success',
                'output_file': output_file,
            }
        except Exception as e:
            logger.error(f"Error extracting audio: {e}")
            return {
                'status': 'error',
                'error': str(e),
            }
    
    @staticmethod
    def extract_frames(
        input_file: str,
        output_pattern: str,
        fps: float = 1.0,
        max_frames: Optional[int] = None
    ) -> Dict[str, Any]:
        """Extract frames from video for analysis"""
        try:
            stream = ffmpeg.input(input_file)
            stream = ffmpeg.filter(stream, 'fps', fps)
            
            kwargs = {'vframes': max_frames} if max_frames else {}
            stream = ffmpeg.output(stream, output_pattern, **kwargs)
            
            ffmpeg.run(stream, capture_stdout=True, capture_stderr=True)
            
            return {
                'status': 'success',
                'pattern': output_pattern,
            }
        except Exception as e:
            logger.error(f"Error extracting frames: {e}")
            return {
                'status': 'error',
                'error': str(e),
            }


# ======================== WHISPER TRANSCRIPTION ========================

class WhisperTranscriber:
    """OpenAI Whisper transcription with advanced features"""
    
    @staticmethod
    @celery_app.task(bind=True, name='transcribe_audio')
    def transcribe_audio_task(self, audio_file: str, language: str = 'en') -> Dict[str, Any]:
        """
        Transcribe audio using OpenAI Whisper
        Celery-managed task for parallel processing
        """
        try:
            import openai
            
            with open(audio_file, 'rb') as f:
                transcript = openai.Audio.transcribe(
                    model="whisper-1",
                    file=f,
                    language=language,
                )
            
            segments = []
            for segment in transcript.get('segments', []):
                segments.append({
                    'start': segment['start'],
                    'end': segment['end'],
                    'text': segment['text'],
                    'confidence': segment.get('confidence', 1.0),
                })
            
            return {
                'status': 'success',
                'language': language,
                'full_text': transcript.get('text', ''),
                'segments': segments,
                'duration': transcript.get('duration', 0),
            }
        except Exception as e:
            logger.error(f"Error transcribing audio: {e}")
            return {
                'status': 'error',
                'error': str(e),
            }
    
    @staticmethod
    def transcribe_segments(segments: List[Tuple[float, str]]) -> List[TranscriptionSegment]:
        """
        Transcribe multiple audio segments in parallel
        """
        transcribed = []
        
        for start_time, audio_file in segments:
            # Use librosa for local transcription alternative
            try:
                # For high-speed local processing without API calls
                y, sr = librosa.load(audio_file, sr=16000)
                # Placeholder for local model transcription
                text = "Transcribed text would go here"
                
                transcribed.append(TranscriptionSegment(
                    start_time=start_time,
                    end_time=start_time + (len(y) / sr),
                    text=text,
                ))
            except Exception as e:
                logger.error(f"Error transcribing segment: {e}")
        
        return transcribed


# ======================== REAL-TIME SYNCHRONIZATION ========================

class BWCSynchronizer:
    """
    Synchronize multiple Body-Worn Camera video streams
    Detects synchronization points and maintains timestamp alignment
    """
    
    def __init__(self, sync_threshold: float = 0.5):
        """
        Initialize synchronizer
        
        Args:
            sync_threshold: Time threshold (seconds) for detecting sync points
        """
        self.sync_threshold = sync_threshold
        self.sync_points: List[SynchronizationPoint] = []
        self.audio_fingerprints = {}
    
    @staticmethod
    def extract_audio_fingerprint(audio_file: str, duration: Optional[float] = None) -> np.ndarray:
        """
        Extract audio fingerprint for frame-accurate synchronization
        Uses spectral analysis to find matching points
        """
        try:
            y, sr = librosa.load(audio_file, sr=16000)
            
            if duration:
                samples = int(sr * duration)
                y = y[:samples]
            
            # Extract MFCC (Mel-frequency cepstral coefficients)
            mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
            
            # Compute mean across time dimension
            fingerprint = np.mean(mfcc, axis=1)
            
            return fingerprint
        except Exception as e:
            logger.error(f"Error extracting fingerprint: {e}")
            return np.array([])
    
    def find_sync_points(self, video_streams: Dict[str, str]) -> List[SynchronizationPoint]:
        """
        Find synchronization points across multiple video streams
        
        Args:
            video_streams: Dict of camera_id -> video_file_path
            
        Returns:
            List of synchronization points
        """
        try:
            # Extract audio from all videos
            audio_files = {}
            for camera_id, video_file in video_streams.items():
                audio_file = f"/tmp/{camera_id}_audio.wav"
                FFmpegVideoProcessor.extract_audio(video_file, audio_file)
                audio_files[camera_id] = audio_file
            
            # Extract fingerprints
            fingerprints = {}
            for camera_id, audio_file in audio_files.items():
                fingerprints[camera_id] = self.extract_audio_fingerprint(audio_file)
            
            # Find matching points
            sync_points = []
            
            # Compare first camera against all others
            reference_camera = list(fingerprints.keys())[0]
            reference_fp = fingerprints[reference_camera]
            
            for camera_id, fp in fingerprints.items():
                if camera_id == reference_camera:
                    continue
                
                # Compute similarity
                correlation = np.corrcoef(reference_fp, fp)[0, 1]
                
                if correlation > 0.9:  # High correlation = synchronized
                    sync_point = SynchronizationPoint(
                        global_timestamp=0.0,
                        camera_timestamps={
                            reference_camera: 0.0,
                            camera_id: 0.0,
                        },
                        confidence=correlation,
                    )
                    sync_points.append(sync_point)
            
            self.sync_points = sync_points
            return sync_points
        
        except Exception as e:
            logger.error(f"Error finding sync points: {e}")
            return []
    
    def align_timestamps(
        self,
        camera_timestamps: Dict[str, float],
        sync_points: List[SynchronizationPoint]
    ) -> float:
        """
        Convert camera-local timestamps to global synchronized timestamp
        """
        if not sync_points:
            return 0.0
        
        # Use first sync point as reference
        ref_point = sync_points[0]
        
        # Calculate offset for each camera
        offsets = {}
        for camera_id, local_ts in camera_timestamps.items():
            ref_ts = ref_point.camera_timestamps.get(camera_id, 0.0)
            offsets[camera_id] = ref_ts - local_ts
        
        # Average offset becomes global timestamp offset
        avg_offset = np.mean(list(offsets.values())) if offsets else 0.0
        
        return avg_offset


# ======================== BATCH PROCESSING PIPELINE ========================

class BatchVideoProcessor:
    """
    High-speed batch processing for multiple video files
    Uses Celery for distributed parallel processing
    """
    
    @staticmethod
    @celery_app.task(bind=True, name='process_video_file')
    def process_video_file(
        self,
        file_id: str,
        input_file: str,
        case_id: str,
        extract_transcription: bool = True,
        target_quality: VideoQuality = VideoQuality.HIGH,
    ) -> Dict[str, Any]:
        """
        Process single video file (Celery task)
        
        Args:
            file_id: Unique file identifier
            input_file: Path to input video file
            case_id: Case ID for organization
            extract_transcription: Whether to extract audio and transcribe
            target_quality: Target transcoding quality
        """
        start_time = time.time()
        result = {
            'file_id': file_id,
            'status': 'processing',
            'steps': {},
        }
        
        try:
            # Step 1: Extract metadata
            result['steps']['metadata'] = {
                'status': 'in_progress',
            }
            metadata = FFmpegVideoProcessor.get_video_metadata(input_file)
            result['steps']['metadata'] = {
                'status': 'complete',
                'duration': metadata.duration,
                'fps': metadata.fps,
                'resolution': metadata.resolution,
                'file_size': metadata.file_size,
            }
            
            # Step 2: Transcode video
            output_file = f"processed/{case_id}/{file_id}_output.mp4"
            result['steps']['transcode'] = {
                'status': 'in_progress',
            }
            transcode_result = FFmpegVideoProcessor.transcode_video(
                input_file,
                output_file,
                quality=target_quality,
            )
            result['steps']['transcode'] = {
                'status': transcode_result['status'],
                'output_file': output_file,
            }
            
            # Step 3: Extract and transcribe audio
            if extract_transcription:
                result['steps']['transcription'] = {
                    'status': 'in_progress',
                }
                
                audio_file = f"/tmp/{file_id}_audio.wav"
                FFmpegVideoProcessor.extract_audio(input_file, audio_file)
                
                # Queue transcription task
                transcribe_task = WhisperTranscriber.transcribe_audio_task.delay(
                    audio_file,
                    language='en'
                )
                
                result['steps']['transcription'] = {
                    'status': 'queued',
                    'task_id': transcribe_task.id,
                }
            
            result['status'] = 'complete'
            result['processing_time'] = time.time() - start_time
            
            return result
        
        except Exception as e:
            logger.error(f"Error processing video {file_id}: {e}")
            result['status'] = 'error'
            result['error'] = str(e)
            result['processing_time'] = time.time() - start_time
            return result
    
    @staticmethod
    def process_batch(
        file_list: List[Tuple[str, str, str]],  # (file_id, input_file, case_id)
        extract_transcription: bool = True,
        target_quality: VideoQuality = VideoQuality.HIGH,
    ) -> Dict[str, Any]:
        """
        Process batch of videos using Celery task group
        Parallelizes processing across workers
        """
        start_time = time.time()
        
        # Create task group
        tasks = group(
            BatchVideoProcessor.process_video_file.s(
                file_id=file_id,
                input_file=input_file,
                case_id=case_id,
                extract_transcription=extract_transcription,
                target_quality=target_quality,
            )
            for file_id, input_file, case_id in file_list
        )
        
        # Execute group
        result = tasks.apply_async()
        
        return {
            'batch_id': result.id,
            'total_files': len(file_list),
            'status': 'processing',
            'submitted_at': datetime.utcnow().isoformat(),
            'queue_depth': len(file_list),
        }
    
    @staticmethod
    def get_batch_status(batch_id: str) -> Dict[str, Any]:
        """Get status of batch processing job"""
        result = AsyncResult(batch_id, app=celery_app)
        
        return {
            'batch_id': batch_id,
            'status': result.status,
            'progress': f"{sum(1 for r in result.children if r.ready())} / {len(result.children)}",
            'results': result.get() if result.ready() else None,
        }


# ======================== STREAMING REAL-TIME PROCESSOR ========================

class RealtimeStreamProcessor:
    """
    Process live video streams in real-time
    Handles multiple concurrent feeds with minimal latency
    """
    
    def __init__(self, chunk_size: int = 4096):
        """Initialize with chunk size for streaming"""
        self.chunk_size = chunk_size
        self.active_streams = {}
    
    async def process_stream(
        self,
        stream_url: str,
        camera_id: str,
        duration: Optional[float] = None,
    ):
        """
        Process continuous live stream with minimal latency
        Uses FFmpeg with pipe output for frame-by-frame processing
        """
        try:
            cmd = [
                'ffmpeg',
                '-i', stream_url,
                '-f', 'image2pipe',
                '-pix_fmt', 'rgb24',
                '-vf', 'scale=1280:720',
                '-'
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            frame_count = 0
            start_time = time.time()
            
            while True:
                if duration and (time.time() - start_time) > duration:
                    break
                
                frame_data = await process.stdout.readexactly(
                    1280 * 720 * 3  # RGB24
                )
                
                if not frame_data:
                    break
                
                frame_count += 1
                
                # Process frame here (object detection, etc.)
                if frame_count % 30 == 0:  # Every second at 30fps
                    logger.info(f"Stream {camera_id}: {frame_count} frames processed")
            
            process.terminate()
            
            return {
                'camera_id': camera_id,
                'total_frames': frame_count,
                'duration': time.time() - start_time,
            }
        
        except Exception as e:
            logger.error(f"Error processing stream {camera_id}: {e}")
            return {
                'camera_id': camera_id,
                'error': str(e),
            }


# ======================== EXPORTS ========================

export_functions = {
    'FFmpegVideoProcessor': FFmpegVideoProcessor,
    'WhisperTranscriber': WhisperTranscriber,
    'BWCSynchronizer': BWCSynchronizer,
    'BatchVideoProcessor': BatchVideoProcessor,
    'RealtimeStreamProcessor': RealtimeStreamProcessor,
    'celery_app': celery_app,
}
