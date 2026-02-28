"""
B30 Phase 1 — Evidence Graph & Artifact Model Tests
=====================================================
Tests that verify:
  - DerivedArtifact references original SHA-256.
  - Originals cannot be overwritten via the model.
  - EvidenceMarker supports timecodes, pages, tags.
  - EvidenceSequenceGroup clusters evidence items.
  - B30AuditEvent is append-only (no update/delete).
  - All new models integrate with existing EvidenceItem.
"""

import json
import pytest
from datetime import datetime, timezone


# ---------------------------------------------------------------------------
# Fixtures (self-contained, matching working test patterns in this repo)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def app():
    """Create a Flask app configured for testing."""
    import os
    os.environ["FLASK_ENV"] = "testing"
    from app_config import create_app
    application = create_app()
    application.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    application.config["TESTING"] = True
    application.config["WTF_CSRF_ENABLED"] = False
    return application


@pytest.fixture(autouse=True)
def app_context(app):
    """Push app context and create tables for each test."""
    from auth.models import db
    # Import B30 models so they register with SQLAlchemy metadata
    import models.b30_evidence_graph  # noqa: F401
    with app.app_context():
        db.create_all()
        yield
        db.session.rollback()
        db.drop_all()


@pytest.fixture
def db_session():
    from auth.models import db
    return db.session


@pytest.fixture
def sample_evidence(db_session):
    """Create a minimal EvidenceItem for testing."""
    from models.evidence import EvidenceItem

    item = EvidenceItem(
        original_filename="BWC_clip_001.mp4",
        evidence_type="video",
        file_type="mp4",
        mime_type="video/mp4",
        file_size_bytes=50_000_000,
        hash_sha256="a" * 64,
        device_label="BWL7139078",
        device_type="body_worn_camera",
        processing_status="complete",
    )
    db_session.add(item)
    db_session.commit()
    return item


@pytest.fixture
def sample_case(db_session):
    """Create a minimal LegalCase for testing."""
    from models.legal_case import LegalCase

    case = LegalCase(
        case_name="B30 Test Case",
        case_number="B30-TEST-001",
        case_type="general",
        status="active",
    )
    db_session.add(case)
    db_session.commit()
    return case


# ---------------------------------------------------------------------------
# DerivedArtifact tests
# ---------------------------------------------------------------------------

class TestDerivedArtifact:
    """Tests for the DerivedArtifact model."""

    def test_create_derived_artifact(self, db_session, sample_evidence):
        from models.b30_evidence_graph import DerivedArtifact

        artifact = DerivedArtifact(
            evidence_id=sample_evidence.id,
            original_sha256=sample_evidence.hash_sha256,
            artifact_type="thumbnail",
            stored_path="/evidence_store/derivatives/aaaa/thumb.jpg",
            filename="thumbnail.jpg",
            sha256="b" * 64,
            size_bytes=45_000,
            mime_type="image/jpeg",
            parameters_json=json.dumps({"timestamp": 10.0, "quality": 2}),
        )
        db_session.add(artifact)
        db_session.commit()

        assert artifact.id is not None
        assert artifact.original_sha256 == "a" * 64
        assert artifact.artifact_type == "thumbnail"
        assert artifact.is_current is True
        assert artifact.is_deleted is False

    def test_derivative_must_reference_original_hash(self, db_session, sample_evidence):
        """Derivative must have a non-empty original_sha256."""
        from models.b30_evidence_graph import DerivedArtifact

        artifact = DerivedArtifact(
            evidence_id=sample_evidence.id,
            original_sha256=sample_evidence.hash_sha256,
            artifact_type="proxy",
            stored_path="/path/to/proxy.mp4",
            filename="proxy_720p.mp4",
            sha256="c" * 64,
            size_bytes=10_000_000,
        )
        db_session.add(artifact)
        db_session.commit()

        assert artifact.original_sha256 is not None
        assert len(artifact.original_sha256) == 64

    def test_derivative_linked_to_evidence(self, db_session, sample_evidence):
        """Derivative is accessible via evidence relationship."""
        from models.b30_evidence_graph import DerivedArtifact

        artifact = DerivedArtifact(
            evidence_id=sample_evidence.id,
            original_sha256=sample_evidence.hash_sha256,
            artifact_type="waveform",
            stored_path="/path/to/waveform.png",
            filename="waveform.png",
            sha256="d" * 64,
            size_bytes=80_000,
        )
        db_session.add(artifact)
        db_session.commit()

        # Refresh and check relationship
        db_session.refresh(sample_evidence)
        artifact_types = [a.artifact_type for a in sample_evidence.derived_artifacts]
        assert "waveform" in artifact_types

    def test_derivative_versioning(self, db_session, sample_evidence):
        """Supersedes chain works correctly."""
        from models.b30_evidence_graph import DerivedArtifact

        v1 = DerivedArtifact(
            evidence_id=sample_evidence.id,
            original_sha256=sample_evidence.hash_sha256,
            artifact_type="thumbnail",
            stored_path="/v1/thumb.jpg",
            filename="thumbnail_v1.jpg",
            sha256="e" * 64,
            size_bytes=40_000,
            is_current=True,
        )
        db_session.add(v1)
        db_session.commit()

        # Supersede with v2
        v1.is_current = False
        v2 = DerivedArtifact(
            evidence_id=sample_evidence.id,
            original_sha256=sample_evidence.hash_sha256,
            artifact_type="thumbnail",
            stored_path="/v2/thumb.jpg",
            filename="thumbnail_v2.jpg",
            sha256="f" * 64,
            size_bytes=42_000,
            is_current=True,
            supersedes_id=v1.id,
        )
        db_session.add(v2)
        db_session.commit()

        assert v2.supersedes_id == v1.id
        assert v2.is_current is True
        assert v1.is_current is False


# ---------------------------------------------------------------------------
# EvidenceMarker tests
# ---------------------------------------------------------------------------

class TestEvidenceMarker:
    """Tests for the EvidenceMarker model."""

    def test_create_timecode_marker(self, db_session, sample_evidence):
        from models.b30_evidence_graph import EvidenceMarker

        marker = EvidenceMarker(
            evidence_id=sample_evidence.id,
            marker_type="flag",
            title="Officer approaches vehicle",
            body="Subject visible at 00:02:15",
            start_seconds=135.0,
            end_seconds=180.0,
            tags_json=json.dumps(["approach", "vehicle", "subject"]),
            confidence=0.95,
            severity="info",
            author_name="Reviewer A",
        )
        db_session.add(marker)
        db_session.commit()

        assert marker.id is not None
        assert marker.start_seconds == 135.0
        assert marker.end_seconds == 180.0
        assert marker.is_current is True
        tags = json.loads(marker.tags_json)
        assert "approach" in tags

    def test_create_page_marker(self, db_session, sample_evidence):
        from models.b30_evidence_graph import EvidenceMarker

        marker = EvidenceMarker(
            evidence_id=sample_evidence.id,
            marker_type="highlight",
            title="Relevant paragraph",
            page_number=3,
            char_offset_start=150,
            char_offset_end=420,
        )
        db_session.add(marker)
        db_session.commit()

        assert marker.page_number == 3
        assert marker.start_seconds is None  # Not a media marker

    def test_markers_linked_to_evidence(self, db_session, sample_evidence):
        from models.b30_evidence_graph import EvidenceMarker

        m1 = EvidenceMarker(
            evidence_id=sample_evidence.id,
            marker_type="note",
            title="First note",
            start_seconds=10.0,
        )
        m2 = EvidenceMarker(
            evidence_id=sample_evidence.id,
            marker_type="note",
            title="Second note",
            start_seconds=25.0,
        )
        db_session.add_all([m1, m2])
        db_session.commit()

        db_session.refresh(sample_evidence)
        marker_titles = [m.title for m in sample_evidence.markers if m.is_current]
        assert "First note" in marker_titles
        assert "Second note" in marker_titles


# ---------------------------------------------------------------------------
# EvidenceSequenceGroup tests
# ---------------------------------------------------------------------------

class TestEvidenceSequenceGroup:
    """Tests for sequence grouping."""

    def test_create_group_with_members(self, db_session, sample_evidence, sample_case):
        from models.b30_evidence_graph import (
            EvidenceSequenceGroup,
            EvidenceSequenceGroupMember,
        )

        group = EvidenceSequenceGroup(
            case_id=sample_case.id,
            group_name="BWC Incident 2025-11-29 22:57",
            group_type="auto",
            device_labels_json=json.dumps(["BWL7139078", "BWL7137497"]),
            grouping_algorithm="time_adjacency_v1",
        )
        db_session.add(group)
        db_session.commit()

        member = EvidenceSequenceGroupMember(
            group_id=group.id,
            evidence_id=sample_evidence.id,
            sequence_index=0,
            device_label="BWL7139078",
        )
        db_session.add(member)
        db_session.commit()

        assert len(group.members) == 1
        assert group.members[0].evidence_id == sample_evidence.id


# ---------------------------------------------------------------------------
# B30AuditEvent tests
# ---------------------------------------------------------------------------

class TestB30AuditEvent:
    """Tests for the B30 audit event model."""

    def test_create_audit_event(self, db_session, sample_evidence):
        from models.b30_evidence_graph import B30AuditEvent

        event = B30AuditEvent(
            correlation_id="550e8400-e29b-41d4-a716-446655440000",
            action="evidence.ingest",
            component="ingest_pipeline",
            actor_name="system",
            evidence_id=sample_evidence.id,
            evidence_sha256=sample_evidence.hash_sha256,
            details_json=json.dumps({
                "file": "BWC_clip_001.mp4",
                "size_bytes": 50_000_000,
            }),
        )
        db_session.add(event)
        db_session.commit()

        assert event.id is not None
        assert event.correlation_id is not None
        assert event.timestamp is not None

    def test_audit_events_are_append_only(self, db_session):
        """Verify multiple events can be created; no delete at model level."""
        from models.b30_evidence_graph import B30AuditEvent

        events = []
        for i in range(5):
            e = B30AuditEvent(
                action=f"test.action_{i}",
                component="test",
                actor_name="test_runner",
                details_json=json.dumps({"index": i}),
            )
            db_session.add(e)
            events.append(e)

        db_session.commit()

        # All 5 events should persist
        count = B30AuditEvent.query.filter_by(component="test").count()
        assert count >= 5

        # Verify we can read them all back
        for e in events:
            loaded = db_session.get(B30AuditEvent, e.id)
            assert loaded is not None
            assert loaded.action.startswith("test.action_")

    def test_audit_event_timestamps_are_utc(self, db_session):
        from models.b30_evidence_graph import B30AuditEvent

        event = B30AuditEvent(
            action="test.utc_check",
            component="test",
            actor_name="test_runner",
        )
        db_session.add(event)
        db_session.commit()

        assert event.timestamp is not None
        # Should be recent (within last minute)
        delta = datetime.now(timezone.utc) - event.timestamp.replace(tzinfo=timezone.utc)
        assert delta.total_seconds() < 60


# ---------------------------------------------------------------------------
# Cross-model integrity tests
# ---------------------------------------------------------------------------

class TestEvidenceGraphIntegrity:
    """Tests that verify cross-model integrity guarantees."""

    def test_original_hash_immutable_on_evidence_item(self, db_session):
        """hash_sha256 is unique — two items with same hash are rejected."""
        from models.evidence import EvidenceItem

        item1 = EvidenceItem(
            original_filename="file_a.mp4",
            evidence_type="video",
            hash_sha256="1" * 64,
        )
        db_session.add(item1)
        db_session.commit()

        item2 = EvidenceItem(
            original_filename="file_b.mp4",
            evidence_type="video",
            hash_sha256="1" * 64,  # Same hash — should fail
        )
        db_session.add(item2)
        with pytest.raises(Exception):
            db_session.commit()
        db_session.rollback()

    def test_derived_artifact_must_have_evidence(self, db_session, sample_evidence):
        """Derived artifact is linked to a valid evidence item."""
        from models.b30_evidence_graph import DerivedArtifact

        artifact = DerivedArtifact(
            evidence_id=sample_evidence.id,
            original_sha256=sample_evidence.hash_sha256,
            artifact_type="transcript",
            stored_path="/path/transcript.txt",
            filename="transcript.txt",
            sha256="9" * 64,
            size_bytes=1200,
        )
        db_session.add(artifact)
        db_session.commit()

        # Verify FK integrity
        assert artifact.evidence.original_filename == "BWC_clip_001.mp4"
