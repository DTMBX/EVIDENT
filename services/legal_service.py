"""
Legal Case Management Service
High-level service layer for case operations, discovery compliance, and legal workflows
"""

from datetime import datetime, timedelta
from models.legal_case import LegalCase, CaseParty, Organization
from models.evidence import (
    EvidenceItem, ChainOfCustody, EvidenceAnalysis, PrivilegeLog,
    ProductionSet, ProductionItem
)
from auth.models import db, User
import hashlib
import json


class LegalCaseService:
    """Service for managing legal cases"""
    
    @staticmethod
    def create_case(case_data, created_by_user):
        """Create a new legal case"""
        case = LegalCase(
            case_number=case_data['case_number'],
            case_name=case_data['case_name'],
            case_type=case_data['case_type'],
            description=case_data.get('description'),
            jurisdiction=case_data.get('jurisdiction'),
            court_name=case_data.get('court_name'),
            judge_name=case_data.get('judge_name'),
            filed_date=case_data.get('filed_date'),
            incident_date=case_data.get('incident_date'),
            discovery_deadline=case_data.get('discovery_deadline'),
            trial_date=case_data.get('trial_date'),
            created_by_id=created_by_user.id
        )
        
        db.session.add(case)
        db.session.commit()
        
        # Log in chain of custody
        ChainOfCustodyService.log_case_action(
            case_id=case.id,
            action='case_created',
            actor_id=created_by_user.id,
            details=f'Case {case.case_number} created'
        )
        
        return case
    
    @staticmethod
    def get_case(case_id):
        """Retrieve case by ID"""
        return LegalCase.query.get(case_id)
    
    @staticmethod
    def update_case(case_id, case_data, updated_by_user):
        """Update case information"""
        case = LegalCase.query.get(case_id)
        if not case:
            return None
        
        # Update fields
        for key, value in case_data.items():
            if hasattr(case, key) and key not in ['id', 'created_at', 'created_by_id']:
                setattr(case, key, value)
        
        case.updated_at = datetime.utcnow()
        db.session.commit()
        
        return case
    
    @staticmethod
    def place_legal_hold(case_id, hold_reason, by_user):
        """Place a legal hold on the case"""
        case = LegalCase.query.get(case_id)
        if not case:
            return None
        
        case.is_legal_hold = True
        case.legal_hold_date = datetime.utcnow()
        
        # Mark all evidence items under legal hold
        for item in case.evidence_items:
            item.is_under_legal_hold = True
        
        db.session.commit()
        
        ChainOfCustodyService.log_case_action(
            case_id=case_id,
            action='legal_hold_placed',
            actor_id=by_user.id,
            details=hold_reason
        )
        
        return case
    
    @staticmethod
    def add_case_party(case_id, party_data):
        """Add a party to the case"""
        party = CaseParty(
            case_id=case_id,
            name=party_data['name'],
            party_type=party_data.get('party_type'),
            role=party_data.get('role'),
            contact_info=party_data.get('contact_info'),
            email=party_data.get('email'),
            phone=party_data.get('phone'),
            notes=party_data.get('notes')
        )
        db.session.add(party)
        db.session.commit()
        return party
    
    @staticmethod
    def get_case_parties(case_id):
        """Get all parties for a case"""
        return CaseParty.query.filter_by(case_id=case_id).all()
    
    @staticmethod
    def get_case_evidence(case_id):
        """Get all evidence items for a case"""
        return EvidenceItem.query.filter_by(case_id=case_id).all()
    
    @staticmethod
    def get_privilege_log(case_id):
        """Get privilege log for a case"""
        return PrivilegeLog.query.filter_by(case_id=case_id).all()


class EvidenceProcessingService:
    """Service for processing and analyzing evidence"""
    
    @staticmethod
    def ingest_evidence(case_id, file_info, uploaded_by_user, collected_date=None):
        """
        Ingest evidence into the system
        Calculates forensic hash and initiates chain of custody tracking
        """
        # Calculate hash for forensic verification
        sha256_hash = file_info.get('sha256') or EvidenceProcessingService.calculate_hash(file_info['filepath'])
        
        evidence = EvidenceItem(
            case_id=case_id,
            original_filename=file_info['filename'],
            stored_filename=file_info.get('stored_filename'),
            file_type=file_info.get('extension'),
            file_size_bytes=file_info.get('size_bytes'),
            mime_type=file_info.get('mime_type'),
            evidence_type=EvidenceProcessingService.classify_evidence_type(file_info.get('extension')),
            media_category=file_info.get('media_category'),
            hash_sha256=sha256_hash,
            collected_date=collected_date or datetime.utcnow(),
            collected_by=file_info.get('collected_by'),
            collection_location=file_info.get('collection_location'),
            upload_by_id=uploaded_by_user.id,
            processing_status='pending'
        )
        
        db.session.add(evidence)
        db.session.commit()
        
        # Log in chain of custody
        ChainOfCustodyService.log_evidence_action(
            evidence_id=evidence.id,
            action='ingested',
            actor_id=uploaded_by_user.id,
            details=f'Evidence ingested: {file_info["filename"]} (SHA256: {sha256_hash})',
            hash_after=sha256_hash
        )
        
        return evidence
    
    @staticmethod
    def calculate_hash(filepath, algorithm='sha256'):
        """Calculate cryptographic hash of file"""
        hash_obj = hashlib.new(algorithm)
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()
    
    @staticmethod
    def classify_evidence_type(extension):
        """Classify evidence type by file extension"""
        extension = extension.lower() if extension else ''
        
        video_exts = {'mp4', 'avi', 'mov', 'mkv', 'webm', 'flv', 'wmv'}
        audio_exts = {'mp3', 'wav', 'flac', 'aac', 'wma', 'm4a', 'aiff'}
        image_exts = {'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'tiff', 'svg'}
        doc_exts = {'pdf', 'doc', 'docx', 'txt', 'rtf', 'xlsx', 'xls', 'pptx', 'ppt'}
        
        if extension in video_exts:
            return 'video'
        elif extension in audio_exts:
            return 'audio'
        elif extension in image_exts:
            return 'image'
        elif extension in doc_exts:
            return 'document'
        else:
            return 'other'
    
    @staticmethod
    def flag_evidence_for_analysis(evidence_id, analysis_types):
        """Flag evidence for AI analysis"""
        evidence = EvidenceItem.query.get(evidence_id)
        if not evidence:
            return None
        
        evidence.processing_status = 'queued'
        
        for analysis_type in analysis_types:
            analysis = EvidenceAnalysis(
                evidence_id=evidence_id,
                analysis_type=analysis_type,
                results_json=json.dumps({'status': 'queued'})
            )
            db.session.add(analysis)
        
        db.session.commit()
        return evidence
    
    @staticmethod
    def mark_privileged(evidence_id, privilege_type, privilege_holder):
        """Mark evidence as privileged"""
        evidence = EvidenceItem.query.get(evidence_id)
        if not evidence:
            return None
        
        evidence.has_privilege = True
        evidence.privilege_type = privilege_type
        
        db.session.commit()
        return evidence
    
    @staticmethod
    def mark_responsive(evidence_id, is_responsive):
        """Mark evidence as responsive to discovery"""
        evidence = EvidenceItem.query.get(evidence_id)
        if not evidence:
            return None
        
        evidence.is_responsive = is_responsive
        db.session.commit()
        return evidence


class ChainOfCustodyService:
    """Service for maintaining immutable chain of custody"""
    
    @staticmethod
    def log_evidence_action(evidence_id, action, actor_id, details='', hash_before=None, hash_after=None, ip_address='', user_agent=''):
        """Log an action on evidence"""
        log = ChainOfCustody(
            evidence_id=evidence_id,
            action=action,
            actor_id=actor_id,
            action_details=details,
            hash_before=hash_before,
            hash_after=hash_after,
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.session.add(log)
        db.session.commit()
        return log
    
    @staticmethod
    def log_case_action(case_id, action, actor_id, details=''):
        """Log an action on a case"""
        case = LegalCase.query.get(case_id)
        if case:
            for item in case.evidence_items:
                ChainOfCustodyService.log_evidence_action(
                    evidence_id=item.id,
                    action=f'case_{action}',
                    actor_id=actor_id,
                    details=details
                )
    
    @staticmethod
    def get_evidence_history(evidence_id):
        """Get complete chain of custody for evidence"""
        return ChainOfCustody.query.filter_by(evidence_id=evidence_id).order_by(
            ChainOfCustody.action_timestamp.asc()
        ).all()


class PrivilegeService:
    """Service for managing privilege assertions"""
    
    @staticmethod
    def assert_privilege(case_id, evidence_id, privilege_data, asserted_by_user):
        """Assert privilege over evidence"""
        log = PrivilegeLog(
            case_id=case_id,
            evidence_id=evidence_id,
            privilege_type=privilege_data['privilege_type'],
            privilege_holder=privilege_data.get('privilege_holder'),
            document_identifier=privilege_data.get('document_identifier'),
            privilege_description=privilege_data.get('description'),
            asserted_by_id=asserted_by_user.id
        )
        db.session.add(log)
        db.session.commit()
        return log
    
    @staticmethod
    def get_case_privilege_log(case_id):
        """Get all privilege assertions for a case"""
        return PrivilegeLog.query.filter_by(case_id=case_id).all()
    
    @staticmethod
    def dispute_privilege(privilege_log_id, dispute_reason, resolved_by_user):
        """Mark privilege as disputed"""
        log = PrivilegeLog.query.get(privilege_log_id)
        if log:
            log.is_disputed = True
            log.dispute_resolution = dispute_reason
            log.resolved_date = datetime.utcnow()
            db.session.commit()
        return log


class DiscoveryService:
    """Service for managing discovery and productions"""
    
    @staticmethod
    def create_production_set(case_id, production_data, created_by_user):
        """Create a production set"""
        prod = ProductionSet(
            case_id=case_id,
            production_number=production_data['production_number'],
            description=production_data.get('description'),
            production_request_date=production_data.get('production_request_date'),
            due_date=production_data.get('due_date'),
            produced_by_id=created_by_user.id
        )
        db.session.add(prod)
        db.session.commit()
        return prod
    
    @staticmethod
    def add_to_production(production_set_id, evidence_id, bates_number, is_redacted=False):
        """Add evidence to production set"""
        item = ProductionItem(
            production_set_id=production_set_id,
            evidence_id=evidence_id,
            bates_number=bates_number,
            is_redacted=is_redacted
        )
        db.session.add(item)
        db.session.commit()
        return item
    
    @staticmethod
    def get_production_set(production_set_id):
        """Get production set details"""
        return ProductionSet.query.get(production_set_id)
    
    @staticmethod
    def finalize_production(production_set_id, reviewed_by_user):
        """Finalize a production set"""
        prod = ProductionSet.query.get(production_set_id)
        if prod:
            prod.status = 'ready'
            prod.reviewed_by_id = reviewed_by_user.id
            prod.updated_at = datetime.utcnow()
            db.session.commit()
        return prod
