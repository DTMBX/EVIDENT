"""
B30 — Unified Evidence Graph: Extended Artifact & Marker Models
================================================================
Extends the evidence data model with:

  - DerivedArtifact: tracks all derivative files (proxy, thumbnail, waveform,
    transcript, OCR text, index shard) with full provenance linking back to
    originals via SHA-256.

  - EvidenceMarker: timestamped annotations/notes on evidence items, supporting
    timecodes for media, page numbers for documents, tags, and confidence levels.

  - EvidenceSequenceGroup: groups related evidence items by time adjacency,
    device label, or naming heuristics (BWC dump clustering).

  - AuditEvent: enhanced append-only audit event model with correlation IDs
    for tracing operations across multiple evidence items.

Design principles:
  - No mutation of originals.
  - Every derivative references the original SHA-256.
  - Markers are non-destructive (separate table, never modify evidence).
  - All rows are append-only; soft-delete via is_deleted flag (row never removed).
  - Correlation IDs link related audit events across a batch operation.
"""

from datetime import datetime, timezone
from auth.models import db


# ---------------------------------------------------------------------------
# DerivedArtifact — filesystem derivatives linked to originals
# ---------------------------------------------------------------------------

class DerivedArtifact(db.Model):
    """
    Tracks a derivative file generated from an original evidence item.

    Examples: proxy video, thumbnail, waveform PNG, transcript text,
    OCR extracted text, search index shard.

    Immutable after creation — updates create new rows.  The 'is_current'
    flag marks the latest version for a given (evidence_id, artifact_type).
    """
    __tablename__ = "derived_artifact"

    id = db.Column(db.Integer, primary_key=True)

    # Link to original evidence
    evidence_id = db.Column(
        db.Integer, db.ForeignKey("evidence_item.id"),
        nullable=False, index=True,
    )
    original_sha256 = db.Column(db.String(64), nullable=False, index=True)

    # Artifact identity
    artifact_type = db.Column(db.String(50), nullable=False)
    # Types: thumbnail, proxy, waveform, transcript, ocr_text,
    #        index_shard, metadata_extract, audio_waveform

    # File storage
    stored_path = db.Column(db.String(1000), nullable=False)
    filename = db.Column(db.String(500), nullable=False)
    sha256 = db.Column(db.String(64), nullable=False, index=True)
    size_bytes = db.Column(db.Integer, nullable=False)
    mime_type = db.Column(db.String(100))

    # Generation parameters (deterministic reproduction)
    parameters_json = db.Column(db.Text)
    # e.g., {"codec": "libx264", "crf": 23, "height": 720}

    # Versioning
    is_current = db.Column(db.Boolean, default=True, nullable=False, index=True)
    supersedes_id = db.Column(
        db.Integer, db.ForeignKey("derived_artifact.id"), nullable=True,
    )

    # Audit
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    # Soft-delete (integrity: never remove rows)
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)

    # Relationships
    evidence = db.relationship("EvidenceItem", backref="derived_artifacts")
    created_by = db.relationship("User", foreign_keys=[created_by_id])
    supersedes = db.relationship(
        "DerivedArtifact", remote_side=[id], foreign_keys=[supersedes_id],
    )

    __table_args__ = (
        db.Index(
            "ix_derived_artifact_evidence_type",
            "evidence_id", "artifact_type",
        ),
    )

    def __repr__(self):
        return (
            f"<DerivedArtifact {self.artifact_type} "
            f"evidence={self.evidence_id} sha256={self.sha256[:12]}>"
        )


# ---------------------------------------------------------------------------
# EvidenceMarker — timestamped annotations on evidence
# ---------------------------------------------------------------------------

class EvidenceMarker(db.Model):
    """
    A non-destructive annotation or note on an evidence item.

    For media: references a timecode range (start_seconds, end_seconds).
    For documents: references page number and optional character offset.
    Supports tags, confidence levels, and author attribution.

    Append-only: updates create new rows with `supersedes_id` linking.
    """
    __tablename__ = "evidence_marker"

    id = db.Column(db.Integer, primary_key=True)

    # Link to evidence
    evidence_id = db.Column(
        db.Integer, db.ForeignKey("evidence_item.id"),
        nullable=False, index=True,
    )
    case_id = db.Column(
        db.Integer, db.ForeignKey("legal_case.id"),
        nullable=True, index=True,
    )

    # Position in media
    start_seconds = db.Column(db.Float, nullable=True)
    end_seconds = db.Column(db.Float, nullable=True)

    # Position in document
    page_number = db.Column(db.Integer, nullable=True)
    char_offset_start = db.Column(db.Integer, nullable=True)
    char_offset_end = db.Column(db.Integer, nullable=True)

    # Marker content
    marker_type = db.Column(db.String(50), nullable=False, default="note")
    # Types: note, highlight, flag, issue, redaction_request, tag
    title = db.Column(db.String(300))
    body = db.Column(db.Text)
    tags_json = db.Column(db.Text)  # JSON array of tag strings

    # Confidence / weight
    confidence = db.Column(db.Float, nullable=True)  # 0.0–1.0
    severity = db.Column(db.String(20), nullable=True)  # info, warning, critical

    # Author
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    author_name = db.Column(db.String(300))

    # Versioning (append-only)
    is_current = db.Column(db.Boolean, default=True, nullable=False, index=True)
    supersedes_id = db.Column(
        db.Integer, db.ForeignKey("evidence_marker.id"), nullable=True,
    )

    # Timestamps
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    # Soft-delete
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)

    # Relationships
    evidence = db.relationship("EvidenceItem", backref="markers")
    author = db.relationship("User", foreign_keys=[author_id])
    supersedes = db.relationship(
        "EvidenceMarker", remote_side=[id], foreign_keys=[supersedes_id],
    )

    __table_args__ = (
        db.Index(
            "ix_evidence_marker_evidence_timecode",
            "evidence_id", "start_seconds",
        ),
    )

    def __repr__(self):
        return (
            f"<EvidenceMarker {self.marker_type} "
            f"evidence={self.evidence_id} t={self.start_seconds}>"
        )


# ---------------------------------------------------------------------------
# EvidenceSequenceGroup — clustering related evidence items
# ---------------------------------------------------------------------------

class EvidenceSequenceGroup(db.Model):
    """
    Groups related evidence items that belong to the same incident,
    based on time adjacency, device labels, or naming heuristics.

    Typical use: a BWC folder dump produces multiple clips from the same
    incident — this model clusters them for timeline review.
    """
    __tablename__ = "evidence_sequence_group"

    id = db.Column(db.Integer, primary_key=True)

    case_id = db.Column(
        db.Integer, db.ForeignKey("legal_case.id"),
        nullable=True, index=True,
    )

    # Group identity
    group_name = db.Column(db.String(300), nullable=False)
    group_type = db.Column(db.String(50), default="auto")
    # Types: auto (algorithm-generated), manual, device, time_window

    # Temporal bounds (earliest start, latest end across members)
    start_time = db.Column(db.DateTime, nullable=True)
    end_time = db.Column(db.DateTime, nullable=True)

    # Device provenance
    device_labels_json = db.Column(db.Text)  # JSON array of device labels in group

    # Grouping metadata
    grouping_algorithm = db.Column(db.String(100))
    grouping_parameters_json = db.Column(db.Text)

    # Audit
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    # Relationships
    members = db.relationship(
        "EvidenceSequenceGroupMember",
        backref="group",
        cascade="all, delete-orphan",
    )
    created_by = db.relationship("User", foreign_keys=[created_by_id])

    def __repr__(self):
        return f"<EvidenceSequenceGroup {self.group_name}>"


class EvidenceSequenceGroupMember(db.Model):
    """
    Links an evidence item to a sequence group with ordering metadata.
    """
    __tablename__ = "evidence_sequence_group_member"

    id = db.Column(db.Integer, primary_key=True)

    group_id = db.Column(
        db.Integer,
        db.ForeignKey("evidence_sequence_group.id"),
        nullable=False,
        index=True,
    )
    evidence_id = db.Column(
        db.Integer,
        db.ForeignKey("evidence_item.id"),
        nullable=False,
        index=True,
    )

    # Ordering within the group
    sequence_index = db.Column(db.Integer, nullable=False, default=0)
    device_label = db.Column(db.String(200))
    clip_start_time = db.Column(db.DateTime, nullable=True)

    __table_args__ = (
        db.UniqueConstraint("group_id", "evidence_id", name="uq_sequence_member"),
    )

    evidence = db.relationship("EvidenceItem")

    def __repr__(self):
        return (
            f"<SequenceGroupMember group={self.group_id} "
            f"evidence={self.evidence_id} idx={self.sequence_index}>"
        )


# ---------------------------------------------------------------------------
# B30AuditEvent — enhanced audit event with correlation IDs
# ---------------------------------------------------------------------------

class B30AuditEvent(db.Model):
    """
    Enhanced audit event for B30 pipeline operations.

    Supplements the existing ChainOfCustody model with:
      - Correlation IDs for batch operations.
      - Service/component tracking.
      - Structured details (JSON).
      - Explicit immutability enforcement.

    This table is APPEND-ONLY. No UPDATE or DELETE operations are permitted
    at the application level.
    """
    __tablename__ = "b30_audit_event"

    id = db.Column(db.Integer, primary_key=True)

    # Correlation
    correlation_id = db.Column(db.String(36), nullable=True, index=True)
    # UUID tying related events (e.g., all events from one batch ingest)

    # What happened
    action = db.Column(db.String(100), nullable=False, index=True)
    component = db.Column(db.String(100), nullable=True)
    # e.g., "ingest_pipeline", "chat_assistant", "export_engine"

    # Who / what
    actor_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    actor_name = db.Column(db.String(300))
    ip_address = db.Column(db.String(45))

    # Evidence reference (optional — not all events relate to one item)
    evidence_id = db.Column(
        db.Integer, db.ForeignKey("evidence_item.id"),
        nullable=True, index=True,
    )
    evidence_sha256 = db.Column(db.String(64), nullable=True)

    # Details (structured JSON)
    details_json = db.Column(db.Text)

    # Timestamp (UTC, immutable)
    timestamp = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    # Relationships
    actor = db.relationship("User", foreign_keys=[actor_id])

    def __repr__(self):
        return (
            f"<B30AuditEvent {self.action} "
            f"actor={self.actor_name} t={self.timestamp}>"
        )
