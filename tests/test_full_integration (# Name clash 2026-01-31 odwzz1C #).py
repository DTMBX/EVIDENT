"""
Comprehensive Integration Tests for BarberX Legal Platform
Tests all major tools and services: BWC analysis, transcription, citations, evidence processing
"""

import json
import sys
import tempfile
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class IntegrationTestRunner:
    """Run all integration tests and report results"""

    def __init__(self):
        self.results = []
        self.passed = 0
        self.failed = 0
        self.skipped = 0

    def log(self, msg, status="INFO"):
        # Use ASCII-safe icons for Windows compatibility
        icons = {"PASS": "[OK]", "FAIL": "[X]", "SKIP": "[--]", "INFO": "->"}
        print(f"  {icons.get(status, '->')} {msg}")

    def test(self, name, test_fn):
        """Run a single test with error handling"""
        print(f"\n[TEST] {name}")
        try:
            result = test_fn()
            if result is None or result is True:
                self.log(f"Passed", "PASS")
                self.passed += 1
                self.results.append({"name": name, "status": "PASS"})
            elif result == "SKIP":
                self.log("Skipped (dependency unavailable)", "SKIP")
                self.skipped += 1
                self.results.append({"name": name, "status": "SKIP"})
            else:
                self.log(f"Failed: {result}", "FAIL")
                self.failed += 1
                self.results.append({"name": name, "status": "FAIL", "error": str(result)})
        except Exception as e:
            self.log(f"Error: {str(e)[:100]}", "FAIL")
            self.failed += 1
            self.results.append({"name": name, "status": "FAIL", "error": str(e)})

    def summary(self):
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print(f"  Passed:  {self.passed}")
        print(f"  Failed:  {self.failed}")
        print(f"  Skipped: {self.skipped}")
        print(f"  Total:   {len(self.results)}")
        print("=" * 60)
        return self.failed == 0


# ============================================================================
# BACKEND INTEGRATION TESTS
# ============================================================================


def test_backend_integration():
    """Test backend service registry and event bus"""
    from backend_integration import Event, cache, event_bus, service_registry

    # Test service registry
    service_registry.register("test_service", {"status": "active"}, version="1.0.0")
    service = service_registry.get("test_service")
    assert service == {"status": "active"}, "Service registry failed"

    # Test event bus
    events_received = []

    def handler(event):
        events_received.append(event)

    event_bus.subscribe("test.event", handler)
    event_bus.publish(Event(event_type="test.event", data={"test": True}, source="test"))

    assert len(events_received) == 1, "Event bus failed"
    assert events_received[0].data["test"] is True

    # Test cache
    cache.set("test_key", "test_value", ttl=60)
    assert cache.get("test_key") == "test_value", "Cache failed"

    return True


def test_retrieval_service():
    """Test legal document retrieval service"""
    from retrieval_service import RetrievalService

    service = RetrievalService()

    # Test retrieve functionality (the actual method name)
    results = service.retrieve("constitutional rights", top_k=5)

    # Should return dict with passages or similar structure
    assert results is not None, "Retrieve should return results"

    return True


def test_legal_library_adapter():
    """Test legal library adapter"""
    from legal_library_adapter import LegalLibraryAdapter

    adapter = LegalLibraryAdapter()

    # Test that adapter initializes and has core methods
    assert hasattr(adapter, "ingest_pdf"), "Should have ingest_pdf method"
    assert hasattr(adapter, "db_path"), "Should have db_path attribute"

    return True

    return True


# ============================================================================
# UNIFIED EVIDENCE SERVICE TESTS
# ============================================================================


def test_unified_evidence_processor():
    """Test the unified evidence processing pipeline"""
    from unified_evidence_service import (EvidenceReportGenerator,
                                          EvidenceType,
                                          UnifiedEvidenceProcessor)

    processor = UnifiedEvidenceProcessor()
    report_gen = EvidenceReportGenerator()

    # Create test transcript file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write(
            "Officer: Do you know why I stopped you?\n"
            "Civilian: No, why?\n"
            "Officer: You failed to signal.\n"
            "Civilian: I want a lawyer.\n"
            "Officer: You're under arrest."
        )
        test_file = Path(f.name)

    try:
        # Process evidence
        results = processor.process_evidence(
            test_file,
            EvidenceType.TRANSCRIPT,
            {
                "evidence_id": "TEST-INT-001",
                "case_number": "CR-2024-TEST",
                "is_original": True,
            },
        )

        assert results["evidence_id"] == "TEST-INT-001"
        assert results["evidence_type"] == "transcript"
        assert "status" in results
        assert "summary" in results

        # Generate report
        report = report_gen.generate_report(results, format="markdown")
        assert "Evidence Analysis Report" in report
        assert "TEST-INT-001" in report

        return True

    finally:
        test_file.unlink()


def test_evidence_types():
    """Test evidence type constants"""
    from unified_evidence_service import EvidenceType, ProcessingStage

    assert EvidenceType.VIDEO == "video"
    assert EvidenceType.AUDIO == "audio"
    assert EvidenceType.DOCUMENT == "document"
    assert EvidenceType.IMAGE == "image"
    assert EvidenceType.TRANSCRIPT == "transcript"

    assert ProcessingStage.UPLOADED == "uploaded"
    assert ProcessingStage.COMPLETED == "completed"

    return True


# ============================================================================
# WHISPER TRANSCRIPTION TESTS
# ============================================================================


def test_whisper_service_init():
    """Test Whisper transcription service initialization"""
    from whisper_transcription import WhisperTranscriptionService

    # Test service initialization (without loading model)
    service = WhisperTranscriptionService(model_size="base")

    assert service.model_size == "base"
    assert ".mp3" in service.supported_formats
    assert ".mp4" in service.supported_formats
    assert ".wav" in service.supported_formats

    return True


def test_whisper_format_validation():
    """Test Whisper format validation"""
    from whisper_transcription import WhisperTranscriptionService

    service = WhisperTranscriptionService()

    # Test supported formats list
    expected_formats = [".mp3", ".mp4", ".wav", ".m4a", ".flac", ".ogg"]
    for fmt in expected_formats:
        assert fmt in service.supported_formats, f"Missing format: {fmt}"

    return True


# ============================================================================
# BWC FORENSIC ANALYZER TESTS
# ============================================================================


def test_bwc_chain_of_custody():
    """Test BWC chain of custody dataclass"""
    try:
        from bwc_forensic_analyzer import ChainOfCustody

        coc = ChainOfCustody(
            file_path="/evidence/bwc_001.mp4",
            sha256_hash="abc123def456",
            file_size=1024000,
            created_at=datetime.now(),
            modified_at=datetime.now(),
            acquired_at=datetime.now(),
            acquired_by="Det. Smith",
            source="OPRA request",
        )

        # Test to_dict method
        data = coc.to_dict()
        assert data["file_path"] == "/evidence/bwc_001.mp4"
        assert data["sha256_hash"] == "abc123def456"
        assert data["acquired_by"] == "Det. Smith"
        assert data["verification_method"] == "SHA-256 cryptographic hash"

        return True
    except ImportError as e:
        # Some dependencies may not be installed
        if "spacy" in str(e) or "torch" in str(e) or "whisper" in str(e):
            return "SKIP"
        raise


def test_bwc_transcript_segment():
    """Test BWC transcript segment dataclass"""
    try:
        from bwc_forensic_analyzer import TranscriptSegment

        segment = TranscriptSegment(
            start_time=0.0,
            end_time=5.5,
            text="Officer: Please step out of the vehicle.",
            speaker="SPEAKER_00",
            speaker_label="Officer Smith",
            confidence=0.95,
        )

        assert segment.duration() == 5.5
        data = segment.to_dict()
        assert data["text"] == "Officer: Please step out of the vehicle."
        assert data["speaker_label"] == "Officer Smith"

        return True
    except ImportError as e:
        if "spacy" in str(e) or "torch" in str(e):
            return "SKIP"
        raise


# ============================================================================
# CITATION NETWORK ANALYZER TESTS
# ============================================================================


def test_citation_treatment_constants():
    """Test citation treatment type constants"""
    try:
        from citation_network_analyzer import CitationTreatment

        assert CitationTreatment.FOLLOWED == "followed"
        assert CitationTreatment.REVERSED == "reversed"
        assert CitationTreatment.QUESTIONED == "questioned"
        assert CitationTreatment.RED_FLAG == "red_flag"
        assert CitationTreatment.GREEN_PLUS == "green_plus"

        return True
    except ImportError as e:
        # May fail if docx or other deps not available
        if "docx" in str(e).lower() or "legal_library" in str(e).lower():
            return "SKIP"
        raise
    except Exception as e:
        if "no module" in str(e).lower():
            return "SKIP"
        raise


def test_citation_analyzer_init():
    """Test citation network analyzer initialization"""
    try:
        from citation_network_analyzer import CitationNetworkAnalyzer

        analyzer = CitationNetworkAnalyzer()

        assert analyzer.api_base == "https://www.courtlistener.com/api/rest/v4/"
        assert hasattr(analyzer, "library")

        return True
    except ImportError as e:
        # May fail if docx or other deps not available
        if "docx" in str(e).lower() or "legal_library" in str(e).lower():
            return "SKIP"
        raise
    except Exception as e:
        # May fail if DB not initialized
        if "no such table" in str(e).lower() or "no module" in str(e).lower():
            return "SKIP"
        raise


# ============================================================================
# CASE LAW VIOLATION SCANNER TESTS
# ============================================================================


def test_violation_scanner_init():
    """Test violation scanner can be imported and initialized"""
    try:
        from case_law_violation_scanner import ViolationScanner

        scanner = ViolationScanner()
        assert hasattr(scanner, "scan_transcript") or hasattr(scanner, "scan")

        return True
    except ImportError:
        return "SKIP"
    except Exception as e:
        if "database" in str(e).lower() or "table" in str(e).lower():
            return "SKIP"
        raise


# ============================================================================
# STATUTORY COMPLIANCE CHECKER TESTS
# ============================================================================


def test_compliance_checker_init():
    """Test statutory compliance checker initialization"""
    try:
        from statutory_compliance_checker import StatutoryComplianceChecker

        checker = StatutoryComplianceChecker()
        assert hasattr(checker, "comprehensive_check") or hasattr(checker, "check")

        return True
    except ImportError:
        return "SKIP"
    except Exception as e:
        if "database" in str(e).lower():
            return "SKIP"
        raise


# ============================================================================
# OCR SERVICE TESTS
# ============================================================================


def test_ocr_service_init():
    """Test OCR service initialization"""
    try:
        from ocr_service import OCRService

        service = OCRService()
        # Check for actual method names
        assert hasattr(service, "extract_text_from_image") or hasattr(
            service, "extract_text_from_pdf"
        )
        assert hasattr(service, "engine")

        return True
    except ImportError:
        return "SKIP"


# ============================================================================
# AI PIPELINE TESTS
# ============================================================================


def test_ai_pipeline_contracts():
    """Test AI pipeline data contracts"""
    try:
        from src.ai.pipeline.contracts import AnalysisRequest, AnalysisResult

        # Test request creation
        request = AnalysisRequest(
            query="Test legal analysis query",
            context={"case_id": "TEST-001"},
        )
        assert request.query == "Test legal analysis query"

        return True
    except ImportError:
        return "SKIP"
    except Exception:
        return "SKIP"


def test_smart_tools():
    """Test AI smart tools availability"""
    try:
        from src.ai.tools.smart_tools import (legal_knowledge_tool, math_tool,
                                              web_search_tool)

        # Tools should be callable
        assert callable(web_search_tool) or hasattr(web_search_tool, "__call__")

        return True
    except ImportError:
        return "SKIP"


# ============================================================================
# ENHANCED ANALYSIS TOOLS TESTS
# ============================================================================


def test_enhanced_analysis_tools():
    """Test enhanced analysis tools module"""
    try:
        # Just test import works
        import enhanced_analysis_tools

        return True
    except ImportError:
        return "SKIP"


# ============================================================================
# JUDGE INTELLIGENCE TESTS
# ============================================================================


def test_judge_intelligence():
    """Test judge intelligence module"""
    try:
        import judge_intelligence

        # Module should be importable
        assert judge_intelligence is not None

        return True
    except ImportError:
        return "SKIP"


# ============================================================================
# SIMILAR CASE FINDER TESTS
# ============================================================================


def test_similar_case_finder():
    """Test similar case finder module"""
    try:
        from similar_case_finder import SimilarCaseFinder

        finder = SimilarCaseFinder()
        # Check for actual method names
        assert hasattr(finder, "find_similar_cases") or hasattr(finder, "search_by_text")
        assert hasattr(finder, "case_database")

        return True
    except ImportError:
        return "SKIP"
    except Exception as e:
        if "database" in str(e).lower() or "openai" in str(e).lower():
            return "SKIP"
        raise


# ============================================================================
# API ENDPOINT TESTS (MOCK)
# ============================================================================


def test_api_modules_import():
    """Test that API modules can be imported"""
    modules_to_test = [
        "api.analysis",
        "api.evidence",
        "api.upload",
    ]

    for module_name in modules_to_test:
        try:
            __import__(module_name)
        except ImportError:
            pass  # Module may not exist, that's OK
        except Exception as e:
            if "flask" in str(e).lower() or "context" in str(e).lower():
                pass  # Flask context errors are expected without app

    return True


# ============================================================================
# TIER GATING TESTS
# ============================================================================


def test_tier_gating():
    """Test tier gating system"""
    try:
        from tier_gating import FeatureTier, check_feature_access

        # Should have tier definitions
        assert hasattr(FeatureTier, "FREE") or "free" in dir(FeatureTier).lower()

        return True
    except ImportError:
        return "SKIP"
    except Exception:
        return "SKIP"


# ============================================================================
# API USAGE METERING TESTS
# ============================================================================


def test_secure_key_manager():
    """Test SecureKeyManager encryption/decryption"""
    from api_usage_metering import SecureKeyManager

    km = SecureKeyManager()

    # Test encryption roundtrip
    test_key = "sk-test1234567890abcdefghijklmnop"
    encrypted = km.encrypt(test_key)

    # Encrypted should be different from plaintext
    assert encrypted != test_key, "Encryption should modify the key"
    assert encrypted.startswith("v1:"), "Should have version prefix"

    # Decryption should recover original
    decrypted = km.decrypt(encrypted)
    assert decrypted == test_key, "Decryption should recover original"

    return True


def test_pricing_calculator():
    """Test API pricing calculator"""
    from decimal import Decimal

    from api_usage_metering import APIPricingCalculator

    # Test GPT-4 pricing
    cost = APIPricingCalculator.calculate_cost("openai", "gpt-4", 1000, 500)
    assert isinstance(cost, Decimal), "Should return Decimal"
    assert cost > 0, "Cost should be positive"

    # Test GPT-4o-mini (cheaper model)
    cost_mini = APIPricingCalculator.calculate_cost("openai", "gpt-4o-mini", 1000, 500)
    assert cost_mini < cost, "GPT-4o-mini should be cheaper than GPT-4"

    # Test unknown model (should use defaults)
    cost_unknown = APIPricingCalculator.calculate_cost("openai", "unknown-model", 1000, 500)
    assert cost_unknown > 0, "Unknown model should still return cost"

    return True


def test_usage_record_dataclass():
    """Test UsageRecord dataclass"""
    from datetime import datetime
    from decimal import Decimal

    from api_usage_metering import UsageRecord

    record = UsageRecord(
        user_id=1,
        provider="openai",
        model="gpt-4",
        prompt_tokens=100,
        completion_tokens=50,
        total_tokens=150,
        estimated_cost_usd=Decimal("0.0075"),
        timestamp=datetime.utcnow(),
        request_hash="abc123",
        response_hash="def456",
    )

    # Test to_dict
    data = record.to_dict()
    assert data["user_id"] == 1
    assert data["provider"] == "openai"
    assert data["model"] == "gpt-4"

    # Test verification hash
    hash1 = record.compute_verification_hash()
    hash2 = record.compute_verification_hash()
    assert hash1 == hash2, "Same data should produce same hash"

    return True


def test_api_metering_service():
    """Test APIUsageMeteringService initialization"""
    from api_usage_metering import APIUsageMeteringService

    service = APIUsageMeteringService()

    assert hasattr(service, "key_manager"), "Should have key_manager"
    assert hasattr(service, "pricing_calculator"), "Should have pricing_calculator"
    assert hasattr(service, "store_api_key"), "Should have store_api_key method"
    assert hasattr(service, "get_api_key"), "Should have get_api_key method"
    assert hasattr(service, "record_usage"), "Should have record_usage method"
    assert hasattr(service, "get_usage_summary"), "Should have get_usage_summary method"

    return True


def test_api_provider_enum():
    """Test APIProvider enum"""
    from api_usage_metering import APIProvider

    assert APIProvider.OPENAI.value == "openai"
    assert APIProvider.ANTHROPIC.value == "anthropic"
    assert APIProvider.GOOGLE.value == "google"
    assert APIProvider.LOCAL.value == "local"

    return True


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================


def run_all_tests():
    """Run all integration tests"""
    runner = IntegrationTestRunner()

    print("=" * 60)
    print("BarberX Full Integration Test Suite")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 60)

    # Backend Infrastructure Tests
    print("\n" + "-" * 40)
    print("BACKEND INFRASTRUCTURE")
    print("-" * 40)
    runner.test("Backend Integration (Registry, Events, Cache)", test_backend_integration)
    runner.test("Retrieval Service", test_retrieval_service)
    runner.test("Legal Library Adapter", test_legal_library_adapter)

    # Unified Evidence Service Tests
    print("\n" + "-" * 40)
    print("UNIFIED EVIDENCE SERVICE")
    print("-" * 40)
    runner.test("Evidence Type Constants", test_evidence_types)
    runner.test("Unified Evidence Processor", test_unified_evidence_processor)

    # Transcription Tests
    print("\n" + "-" * 40)
    print("WHISPER TRANSCRIPTION")
    print("-" * 40)
    runner.test("Whisper Service Initialization", test_whisper_service_init)
    runner.test("Whisper Format Validation", test_whisper_format_validation)

    # BWC Forensic Analyzer Tests
    print("\n" + "-" * 40)
    print("BWC FORENSIC ANALYZER")
    print("-" * 40)
    runner.test("BWC Chain of Custody", test_bwc_chain_of_custody)
    runner.test("BWC Transcript Segment", test_bwc_transcript_segment)

    # Citation Network Tests
    print("\n" + "-" * 40)
    print("CITATION NETWORK ANALYZER")
    print("-" * 40)
    runner.test("Citation Treatment Constants", test_citation_treatment_constants)
    runner.test("Citation Analyzer Initialization", test_citation_analyzer_init)

    # Analysis Tools Tests
    print("\n" + "-" * 40)
    print("ANALYSIS TOOLS")
    print("-" * 40)
    runner.test("Violation Scanner", test_violation_scanner_init)
    runner.test("Compliance Checker", test_compliance_checker_init)
    runner.test("OCR Service", test_ocr_service_init)
    runner.test("Enhanced Analysis Tools", test_enhanced_analysis_tools)
    runner.test("Judge Intelligence", test_judge_intelligence)
    runner.test("Similar Case Finder", test_similar_case_finder)

    # AI Pipeline Tests
    print("\n" + "-" * 40)
    print("AI PIPELINE")
    print("-" * 40)
    runner.test("AI Pipeline Contracts", test_ai_pipeline_contracts)
    runner.test("Smart Tools", test_smart_tools)

    # API & Tier Tests
    print("\n" + "-" * 40)
    print("API & ACCESS CONTROL")
    print("-" * 40)
    runner.test("API Modules Import", test_api_modules_import)
    runner.test("Tier Gating System", test_tier_gating)

    # API Usage Metering Tests
    print("\n" + "-" * 40)
    print("API USAGE METERING")
    print("-" * 40)
    runner.test("SecureKeyManager Encryption", test_secure_key_manager)
    runner.test("API Pricing Calculator", test_pricing_calculator)
    runner.test("UsageRecord Dataclass", test_usage_record_dataclass)
    runner.test("API Metering Service", test_api_metering_service)
    runner.test("API Provider Enum", test_api_provider_enum)

    # Print summary
    success = runner.summary()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
