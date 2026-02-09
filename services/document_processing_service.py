"""
Document Processing Service
Service methods for OCR, transcription, redaction, and compliance reviews
"""

from datetime import datetime, timedelta
from models.document_processing import (
    DocumentProcessingTask, OCRResult, TranscriptionResult, RedactionRule,
    RedactionInstance, ComplianceReview, ContentExtractionIndex,
    BatchProcessingQueue
)
from models.evidence import EvidenceItem, ChainOfCustody
from models.legal_case import LegalCase
from auth.models import db, User
import json
from uuid import uuid4


class ProcessingTaskService:
    """Service for managing document processing tasks"""
    
    @staticmethod
    def create_processing_task(evidence_id, case_id, task_type, created_by_user, parameters=None, priority='normal'):
        """Create a new document processing task"""
        task_uuid = str(uuid4())
        
        task = DocumentProcessingTask(
            evidence_id=evidence_id,
            case_id=case_id,
            task_type=task_type,
            task_uuid=task_uuid,
            priority=priority,
            parameters=json.dumps(parameters) if parameters else None,
            requested_by_id=created_by_user.id,
            status='queued'
        )
        
        db.session.add(task)
        db.session.commit()
        
        return task
    
    @staticmethod
    def update_task_status(task_id, new_status, completed_by_user=None, result_data=None, error_message=None):
        """Update processing task status"""
        task = DocumentProcessingTask.query.get(task_id)
        if not task:
            return None
        
        old_status = task.status
        task.status = new_status
        
        if new_status == 'processing' and not task.started_at:
            task.started_at = datetime.utcnow()
        
        if new_status == 'completed':
            task.completed_at = datetime.utcnow()
            if task.started_at:
                task.processing_time_seconds = int((task.completed_at - task.started_at).total_seconds())
            task.result_data = result_data
            task.completed_by_id = completed_by_user.id if completed_by_user else None
        
        if error_message:
            task.error_message = error_message
        
        db.session.commit()
        
        return task
    
    @staticmethod
    def get_task_queue(case_id=None, limit=50):
        """Get pending processing tasks"""
        query = DocumentProcessingTask.query.filter_by(status='queued')
        
        if case_id:
            query = query.filter_by(case_id=case_id)
        
        return query.order_by(
            DocumentProcessingTask.priority.desc(),
            DocumentProcessingTask.queued_at
        ).limit(limit).all()


class OCRService:
    """Service for OCR processing"""
    
    @staticmethod
    def process_ocr_result(evidence_id, task_id, extracted_text, confidence_score=None, pages_processed=None):
        """Store OCR processing results"""
        ocr_result = OCRResult.query.filter_by(evidence_id=evidence_id).first()
        
        if not ocr_result:
            ocr_result = OCRResult(
                evidence_id=evidence_id,
                processing_task_id=task_id,
                extracted_text=extracted_text,
                confidence_per_line='[]',
                pages_processed=pages_processed or 0
            )
            db.session.add(ocr_result)
        else:
            ocr_result.extracted_text = extracted_text
            ocr_result.processing_task_id = task_id
            ocr_result.pages_processed = pages_processed or ocr_result.pages_processed
        
        if confidence_score:
            ocr_result.average_confidence = confidence_score
        
        # Update evidence item
        evidence = EvidenceItem.query.get(evidence_id)
        if evidence:
            evidence.text_content = extracted_text
            evidence.has_ocr = True
            evidence.processing_status = 'completed'
        
        db.session.commit()
        
        return ocr_result
    
    @staticmethod
    def get_ocr_results(evidence_id):
        """Retrieve OCR results for evidence"""
        return OCRResult.query.filter_by(evidence_id=evidence_id).first()


class TranscriptionService:
    """Service for transcription processing"""
    
    @staticmethod
    def create_transcription_result(evidence_id, task_id, transcript_data, created_by_user):
        """Create and store transcription result"""
        transcript = TranscriptionResult(
            evidence_id=evidence_id,
            processing_task_id=task_id,
            full_transcript=transcript_data['full_transcript'],
            duration_seconds=transcript_data.get('duration_seconds'),
            average_confidence=transcript_data.get('confidence', 0.85),
            detected_language=transcript_data.get('language', 'en'),
            speakers_identified=json.dumps(transcript_data.get('speakers', []))
        )
        
        db.session.add(transcript)
        
        # Update evidence item
        evidence = EvidenceItem.query.get(evidence_id)
        if evidence:
            evidence.transcript = transcript_data['full_transcript'].encode('utf-8')
            evidence.has_been_transcribed = True
            evidence.processing_status = 'completed'
        
        db.session.commit()
        
        return transcript
    
    @staticmethod
    def flag_for_review(transcription_id, review_notes):
        """Flag transcription for human review"""
        transcript = TranscriptionResult.query.get(transcription_id)
        if not transcript:
            return None
        
        transcript.requires_review = True
        transcript.review_notes = review_notes
        db.session.commit()
        
        return transcript
    
    @staticmethod
    def approve_transcription(transcription_id, approved_by_user, corrected_text=None):
        """Approve transcription after review"""
        transcript = TranscriptionResult.query.get(transcription_id)
        if not transcript:
            return None
        
        transcript.reviewed_by_id = approved_by_user.id
        transcript.reviewed_at = datetime.utcnow()
        transcript.requires_review = False
        
        if corrected_text:
            transcript.corrected_transcript = corrected_text
            transcript.full_transcript = corrected_text
        
        db.session.commit()
        
        return transcript
    
    @staticmethod
    def get_transcription(evidence_id):
        """Get transcription for evidence"""
        return TranscriptionResult.query.filter_by(evidence_id=evidence_id).first()


class RedactionService:
    """Service for managing redactions"""
    
    @staticmethod
    def create_redaction_rule(case_id, rule_data, created_by_user):
        """Create automated redaction rule"""
        rule = RedactionRule(
            case_id=case_id,
            rule_name=rule_data['rule_name'],
            rule_type=rule_data['rule_type'],
            pattern=rule_data['pattern'],
            entity_type=rule_data.get('entity_type'),
            applies_to_document_types=rule_data.get('applies_to_document_types'),
            applies_to_fields=json.dumps(rule_data.get('applies_to_fields', {})),
            redaction_style=rule_data.get('redaction_style', 'blackout'),
            replacement_text=rule_data.get('replacement_text', '[REDACTED]'),
            created_by_id=created_by_user.id
        )
        
        db.session.add(rule)
        db.session.commit()
        
        return rule
    
    @staticmethod
    def record_redaction(evidence_id, redaction_type, rule_id=None, original_text=None, created_by_user=None):
        """Record a redaction made to a document"""
        redaction = RedactionInstance(
            evidence_id=evidence_id,
            redaction_rule_id=rule_id,
            redaction_type=redaction_type,
            original_text=original_text,
            redaction_method='manual' if not rule_id else 'automatic',
            created_by_id=created_by_user.id if created_by_user else None
        )
        
        db.session.add(redaction)
        
        # Mark evidence as redacted
        evidence = EvidenceItem.query.get(evidence_id)
        if evidence:
            evidence.is_redacted = True
        
        db.session.commit()
        
        return redaction
    
    @staticmethod
    def approve_redaction(redaction_id, approved_by_user):
        """Approve a redaction"""
        redaction = RedactionInstance.query.get(redaction_id)
        if not redaction:
            return None
        
        redaction.is_approved = True
        redaction.approved_by_id = approved_by_user.id
        redaction.approved_at = datetime.utcnow()
        
        db.session.commit()
        
        return redaction
    
    @staticmethod
    def get_redactions_for_evidence(evidence_id, approved_only=False):
        """Get all redactions for evidence item"""
        query = RedactionInstance.query.filter_by(evidence_id=evidence_id)
        
        if approved_only:
            query = query.filter_by(is_approved=True)
        
        return query.all()
    
    @staticmethod
    def get_unapproved_redactions(case_id):
        """Get all unapproved redactions in a case"""
        return RedactionInstance.query.join(EvidenceItem).filter(
            EvidenceItem.case_id == case_id,
            RedactionInstance.is_approved == False
        ).all()


class ComplianceReviewService:
    """Service for compliance reviews and QA"""
    
    @staticmethod
    def create_compliance_review(evidence_id, case_id, review_data, reviewed_by_user):
        """Create a compliance review"""
        review = ComplianceReview(
            evidence_id=evidence_id,
            case_id=case_id,
            review_type=review_data['review_type'],
            review_date=datetime.utcnow(),
            findings=review_data.get('findings'),
            accuracy_score=review_data.get('accuracy_score'),
            completeness_score=review_data.get('completeness_score'),
            compliance_score=review_data.get('compliance_score'),
            has_ocr_errors=review_data.get('has_ocr_errors', False),
            has_transcription_errors=review_data.get('has_transcription_errors', False),
            has_missed_redactions=review_data.get('has_missed_redactions', False),
            has_privilege_issues=review_data.get('has_privilege_issues', False),
            requires_reprocessing=review_data.get('requires_reprocessing', False),
            reprocessing_reason=review_data.get('reprocessing_reason'),
            reviewed_by_id=reviewed_by_user.id
        )
        
        if review_data.get('accuracy_score') and review_data.get('accuracy_score') < 80:
            review.status = 'rejected'
        else:
            review.status = 'approved'
        
        db.session.add(review)
        db.session.commit()
        
        return review
    
    @staticmethod
    def get_case_compliance_summary(case_id):
        """Get compliance review summary for case"""
        reviews = ComplianceReview.query.filter_by(case_id=case_id).all()
        
        summary = {
            'total_reviews': len(reviews),
            'approved': sum(1 for r in reviews if r.status == 'approved'),
            'rejected': sum(1 for r in reviews if r.status == 'rejected'),
            'pending': sum(1 for r in reviews if r.status == 'pending'),
            'average_accuracy': 0,
            'average_compliance': 0,
            'issues_found': 0
        }
        
        if reviews:
            accuracy_scores = [r.accuracy_score for r in reviews if r.accuracy_score]
            compliance_scores = [r.compliance_score for r in reviews if r.compliance_score]
            
            if accuracy_scores:
                summary['average_accuracy'] = sum(accuracy_scores) / len(accuracy_scores)
            if compliance_scores:
                summary['average_compliance'] = sum(compliance_scores) / len(compliance_scores)
            
            summary['issues_found'] = sum(r.issues_found for r in reviews)
        
        return summary


class ContentIndexService:
    """Service for content extraction and indexing"""
    
    @staticmethod
    def create_content_index(evidence_id, case_id, content_data):
        """Create content extraction index entry"""
        index = ContentExtractionIndex(
            evidence_id=evidence_id,
            case_id=case_id,
            content_type=content_data.get('content_type', 'text'),
            word_count=content_data.get('word_count', 0),
            character_count=content_data.get('character_count', 0),
            full_text=content_data.get('full_text'),
            summary=content_data.get('summary'),
            entities_json=json.dumps(content_data.get('entities', {})),
            persons=content_data.get('persons', ''),
            organizations=content_data.get('organizations', ''),
            locations=content_data.get('locations', ''),
            email_addresses=content_data.get('emails', ''),
            phone_numbers=content_data.get('phones', ''),
            key_phrases=json.dumps(content_data.get('key_phrases', [])),
            sentiment=content_data.get('sentiment', 'neutral'),
            is_sensitive=content_data.get('is_sensitive', False)
        )
        
        db.session.add(index)
        db.session.commit()
        
        return index
    
    @staticmethod
    def search_content(case_id, keywords, limit=100):
        """Search indexed content"""
        query = ContentExtractionIndex.query.filter_by(case_id=case_id)
        
        if keywords:
            keyword_filter = '%{}%'.format(keywords)
            query = query.filter(
                (ContentExtractionIndex.full_text.ilike(keyword_filter)) |
                (ContentExtractionIndex.persons.ilike(keyword_filter)) |
                (ContentExtractionIndex.organizations.ilike(keyword_filter)) |
                (ContentExtractionIndex.key_phrases.ilike(keyword_filter))
            )
        
        return query.limit(limit).all()
    
    @staticmethod
    def mark_indexed(evidence_id):
        """Mark content as indexed"""
        index = ContentExtractionIndex.query.filter_by(evidence_id=evidence_id).first()
        if index:
            index.is_indexed = True
            index.last_indexed = datetime.utcnow()
            db.session.commit()
        
        return index


class BatchProcessingService:
    """Service for batch processing operations"""
    
    @staticmethod
    def create_batch_job(case_id, batch_data, created_by_user):
        """Create a batch processing job"""
        batch_uuid = str(uuid4())
        
        batch = BatchProcessingQueue(
            case_id=case_id,
            batch_name=batch_data['batch_name'],
            batch_uuid=batch_uuid,
            processing_type=batch_data['processing_type'],
            document_count=batch_data.get('document_count', 0),
            processing_parameters=json.dumps(batch_data.get('parameters', {})),
            priority=batch_data.get('priority', 'normal'),
            created_by_id=created_by_user.id
        )
        
        db.session.add(batch)
        db.session.commit()
        
        return batch
    
    @staticmethod
    def update_batch_progress(batch_id, successful_count, failed_count, progress_percentage, estimated_completion=None):
        """Update batch job progress"""
        batch = BatchProcessingQueue.query.get(batch_id)
        if not batch:
            return None
        
        batch.successful_count = successful_count
        batch.failed_count = failed_count
        batch.progress_percentage = progress_percentage
        batch.estimated_completion = estimated_completion
        
        if progress_percentage >= 100:
            batch.status = 'completed'
            batch.completed_at = datetime.utcnow()
        
        db.session.commit()
        
        return batch
    
    @staticmethod
    def complete_batch(batch_id, total_cost=None):
        """Mark batch as completed"""
        batch = BatchProcessingQueue.query.get(batch_id)
        if batch:
            batch.status = 'completed'
            batch.completed_at = datetime.utcnow()
            if total_cost:
                batch.actual_total_cost = total_cost
            db.session.commit()
        
        return batch
    
    @staticmethod
    def get_batch_status(batch_id):
        """Get detailed batch status"""
        batch = BatchProcessingQueue.query.get(batch_id)
        if not batch:
            return None
        
        return {
            'batch_id': batch.id,
            'name': batch.batch_name,
            'status': batch.status,
            'progress': batch.progress_percentage,
            'total_documents': batch.document_count,
            'successful': batch.successful_count,
            'failed': batch.failed_count,
            'started': batch.started_at.isoformat() if batch.started_at else None,
            'estimated_completion': batch.estimated_completion.isoformat() if batch.estimated_completion else None,
            'cost': batch.actual_total_cost or batch.estimated_total_cost
        }
