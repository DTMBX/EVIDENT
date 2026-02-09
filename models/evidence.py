"""
Evident Evidence Processing Models
Models for tracking evidence items, chain of custody, and evidence analysis
"""

from datetime import datetime
from auth.models import db, User


class EvidenceItem(db.Model):
    """
    Represents a piece of evidence (document, video, image, audio)
    Tracks all metadata and processing status
    """
    __tablename__ = 'evidence_item'
    
    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey('legal_case.id'), nullable=False)
    
    # File Information
    original_filename = db.Column(db.String(500), nullable=False)
    stored_filename = db.Column(db.String(500))  # Hashed/sanitized name on disk
    file_type = db.Column(db.String(50))  # pdf, mp4, jpg, mp3, docx, etc.
    file_size_bytes = db.Column(db.Integer)
    mime_type = db.Column(db.String(100))
    
    # Evidence Classification
    evidence_type = db.Column(db.String(50), nullable=False)  # document, video, image, audio, other
    media_category = db.Column(db.String(100))  # e.g., body_worn_camera, surveillance, interview
    
    # Metadata & Chain of Custody
    hash_sha256 = db.Column(db.String(64), unique=True, index=True)  # Forensic hash
    hash_md5 = db.Column(db.String(32))
    
    collected_date = db.Column(db.DateTime)
    collected_by = db.Column(db.String(300))  # Officer, investigator name
    collection_location = db.Column(db.String(300))
    
    # Content Information
    duration_seconds = db.Column(db.Integer)  # For video/audio
    transcript = db.Column(db.LargeBinary)  # Transcription if processed
    text_content = db.Column(db.Text)  # Extracted text from PDF/images
    
    # Processing Status
    processing_status = db.Column(db.String(50), default='pending')  # pending, processing, completed, failed
    has_been_transcribed = db.Column(db.Boolean, default=False)
    has_ocr = db.Column(db.Boolean, default=False)
    is_redacted = db.Column(db.Boolean, default=False)
    
    # Discovery Classification
    is_responsive = db.Column(db.Boolean)  # Null = undetermined
    has_privilege = db.Column(db.Boolean, default=False)
    privilege_type = db.Column(db.String(100))  # attorney_client, work_product, spousal, etc.
    
    # Legal Holds & Retention
    is_under_legal_hold = db.Column(db.Boolean, default=False)
    retention_date = db.Column(db.DateTime)
    
    # Audit Trail
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    uploaded_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    notes = db.Column(db.Text)
    
    # Relationships
    uploaded_by = db.relationship('User', foreign_keys=[uploaded_by_id])
    chain_of_custody = db.relationship('ChainOfCustody', backref='evidence', cascade='all, delete-orphan')
    analysis_results = db.relationship('EvidenceAnalysis', backref='evidence', cascade='all, delete-orphan')
    tags = db.relationship('EvidenceTag', secondary='evidence_tag_association', backref='evidence_items')
    
    def __repr__(self):
        return f'<EvidenceItem {self.original_filename}>'


class ChainOfCustody(db.Model):
    """
    Immutable audit log for evidence handling
    Each action creates a new record - no updates
    """
    __tablename__ = 'chain_of_custody'
    
    id = db.Column(db.Integer, primary_key=True)
    evidence_id = db.Column(db.Integer, db.ForeignKey('evidence_item.id'), nullable=False, index=True)
    
    # Action Information
    action = db.Column(db.String(100), nullable=False)  # uploaded, accessed, analyzed, redacted, exported, etc.
    actor_name = db.Column(db.String(300))  # User who performed action
    actor_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Timestamp (immutable)
    action_timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Details
    action_details = db.Column(db.Text)  # JSON or text description
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(500))
    
    # Integrity
    hash_before = db.Column(db.String(64))  # Hash of evidence before action
    hash_after = db.Column(db.String(64))   # Hash of evidence after action
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    actor = db.relationship('User', foreign_keys=[actor_id])
    
    def __repr__(self):
        return f'<ChainOfCustody {self.action} by {self.actor_name}>'


class EvidenceAnalysis(db.Model):
    """
    Results of AI/automated analysis on evidence items
    """
    __tablename__ = 'evidence_analysis'
    
    id = db.Column(db.Integer, primary_key=True)
    evidence_id = db.Column(db.Integer, db.ForeignKey('evidence_item.id'), nullable=False)
    
    # Analysis Type
    analysis_type = db.Column(db.String(100), nullable=False)  # transcription, ocr, entity_extraction, privilege_detection, etc.
    
    # Results
    confidence_score = db.Column(db.Float)  # 0-1 confidence
    results_json = db.Column(db.Text)  # JSON results from analysis
    
    # Processing
    model_name = db.Column(db.String(200))  # e.g., "whisper-v2", "gpt-4-turbo"
    processing_time_seconds = db.Column(db.Integer)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<EvidenceAnalysis {self.analysis_type}>'


class EvidenceTag(db.Model):
    """
    Tags for organizing and categorizing evidence
    """
    __tablename__ = 'evidence_tag'
    
    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey('legal_case.id'), nullable=False)
    
    tag_name = db.Column(db.String(100), nullable=False)
    tag_color = db.Column(db.String(7))  # Hex color
    description = db.Column(db.Text)
    
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    created_by = db.relationship('User', foreign_keys=[created_by_id])
    
    def __repr__(self):
        return f'<EvidenceTag {self.tag_name}>'


# Association table for evidence and tags
evidence_tag_association = db.Table(
    'evidence_tag_association',
    db.Column('evidence_id', db.Integer, db.ForeignKey('evidence_item.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('evidence_tag.id'), primary_key=True),
    db.Column('assigned_at', db.DateTime, default=datetime.utcnow)
)


class PrivilegeLog(db.Model):
    """
    Maintains privilege assertions for disputed productions
    """
    __tablename__ = 'privilege_log'
    
    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey('legal_case.id'), nullable=False)
    
    evidence_id = db.Column(db.Integer, db.ForeignKey('evidence_item.id'))
    
    # Privilege Information
    privilege_type = db.Column(db.String(100), nullable=False)  # attorney_client, work_product, spousal, clergy, etc.
    privilege_holder = db.Column(db.String(300))  # Party claiming privilege
    
    document_identifier = db.Column(db.String(300))  # Bates number or other ID
    document_date = db.Column(db.DateTime)
    
    # Description
    privilege_description = db.Column(db.Text)  # Why privilege applies
    exempt_from_disclosure = db.Column(db.Boolean, default=True)
    
    # Assertion
    asserted_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    asserted_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Dispute Resolution
    is_disputed = db.Column(db.Boolean, default=False)
    dispute_resolution = db.Column(db.Text)
    resolved_date = db.Column(db.DateTime)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    asserted_by = db.relationship('User', foreign_keys=[asserted_by_id])
    
    def __repr__(self):
        return f'<PrivilegeLog {self.privilege_type}>'


class ProductionSet(db.Model):
    """
    Represents a production of documents in response to discovery requests
    """
    __tablename__ = 'production_set'
    
    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey('legal_case.id'), nullable=False)
    
    production_number = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    
    production_request_date = db.Column(db.DateTime)
    production_date = db.Column(db.DateTime, default=datetime.utcnow)
    due_date = db.Column(db.DateTime)
    
    bates_start = db.Column(db.String(50))
    bates_end = db.Column(db.String(50))
    
    item_count = db.Column(db.Integer)
    total_size_bytes = db.Column(db.Integer)
    
    produced_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    reviewed_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    status = db.Column(db.String(50), default='draft')  # draft, ready, produced, received
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    produced_by = db.relationship('User', foreign_keys=[produced_by_id])
    reviewed_by = db.relationship('User', foreign_keys=[reviewed_by_id])
    items = db.relationship('ProductionItem', backref='production_set', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<ProductionSet {self.production_number}>'


class ProductionItem(db.Model):
    """
    Individual evidence items included in a production set
    """
    __tablename__ = 'production_item'
    
    id = db.Column(db.Integer, primary_key=True)
    production_set_id = db.Column(db.Integer, db.ForeignKey('production_set.id'), nullable=False)
    evidence_id = db.Column(db.Integer, db.ForeignKey('evidence_item.id'), nullable=False)
    
    bates_number = db.Column(db.String(50), unique=True)
    
    is_redacted = db.Column(db.Boolean, default=False)
    redaction_notes = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    evidence = db.relationship('EvidenceItem')
    
    def __repr__(self):
        return f'<ProductionItem {self.bates_number}>'
