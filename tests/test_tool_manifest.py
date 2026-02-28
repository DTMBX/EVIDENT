"""
Tests for B30 Phase 8 — Tool Manifest & Registry
==================================================
Validates:
  - ToolManifest immutability and serialization
  - ToolRegistry registration, discovery, and uniqueness
  - Dependency validation and cycle detection
  - Execution plan generation (topological sort)
  - Full BWC pipeline registry (7 tools)
  - JSON export and file save
"""

import json
import hashlib
from pathlib import Path

import pytest

from services.tool_manifest import (
    ToolManifest,
    ToolParam,
    ToolRegistry,
    build_bwc_registry,
)


# ---------------------------------------------------------------------------
# ToolManifest tests
# ---------------------------------------------------------------------------

class TestToolManifest:
    def test_create_manifest(self):
        m = ToolManifest(
            name="test_tool",
            version="1.0.0",
            description="A test tool",
            category="test",
            inputs=(ToolParam("input_a", "string"),),
            outputs=(ToolParam("output_b", "dict"),),
        )
        assert m.name == "test_tool"
        assert m.version == "1.0.0"
        assert m.deterministic is True
        assert m.requires_audit is True

    def test_manifest_is_frozen(self):
        m = ToolManifest(
            name="frozen",
            version="1.0.0",
            description="Immutable",
            category="test",
            inputs=(),
            outputs=(),
        )
        with pytest.raises(AttributeError):
            m.name = "changed"

    def test_to_dict(self):
        m = ToolManifest(
            name="dict_test",
            version="2.0.0",
            description="Dict test",
            category="export",
            inputs=(ToolParam("path", "file", description="File path"),),
            outputs=(ToolParam("hash", "string", description="SHA-256"),),
            dependencies=("dep_a",),
            capabilities=("export", "compress"),
        )
        d = m.to_dict()
        assert d["name"] == "dict_test"
        assert d["category"] == "export"
        assert len(d["inputs"]) == 1
        assert d["inputs"][0]["type"] == "file"
        assert d["dependencies"] == ["dep_a"]
        assert "compress" in d["capabilities"]

    def test_manifest_hash_deterministic(self):
        m = ToolManifest(
            name="hash_test",
            version="1.0.0",
            description="Hash test",
            category="test",
            inputs=(),
            outputs=(),
        )
        assert m.manifest_hash == m.manifest_hash  # Same every time
        assert len(m.manifest_hash) == 64

    def test_different_manifests_different_hashes(self):
        m1 = ToolManifest(
            name="tool_a", version="1.0.0", description="A",
            category="test", inputs=(), outputs=(),
        )
        m2 = ToolManifest(
            name="tool_b", version="1.0.0", description="B",
            category="test", inputs=(), outputs=(),
        )
        assert m1.manifest_hash != m2.manifest_hash


# ---------------------------------------------------------------------------
# ToolRegistry tests
# ---------------------------------------------------------------------------

class TestToolRegistry:
    def _make_manifest(self, name, deps=()):
        return ToolManifest(
            name=name,
            version="1.0.0",
            description=f"Tool {name}",
            category="test",
            inputs=(),
            outputs=(),
            dependencies=deps,
        )

    def test_register_and_get(self):
        reg = ToolRegistry()
        m = self._make_manifest("alpha")
        reg.register(m)
        assert reg.get("alpha") is m
        assert reg.get("nonexistent") is None

    def test_duplicate_registration_rejected(self):
        reg = ToolRegistry()
        reg.register(self._make_manifest("dup"))
        with pytest.raises(ValueError, match="already registered"):
            reg.register(self._make_manifest("dup"))

    def test_list_all(self):
        reg = ToolRegistry()
        reg.register(self._make_manifest("beta"))
        reg.register(self._make_manifest("alpha"))
        names = [m.name for m in reg.list_all()]
        assert names == ["alpha", "beta"]  # Sorted

    def test_tool_count(self):
        reg = ToolRegistry()
        assert reg.tool_count == 0
        reg.register(self._make_manifest("a"))
        reg.register(self._make_manifest("b"))
        assert reg.tool_count == 2

    def test_filter_by_category(self):
        reg = ToolRegistry()
        reg.register(ToolManifest(
            name="ingest_tool", version="1.0.0", description="Ingest",
            category="ingest", inputs=(), outputs=(),
        ))
        reg.register(ToolManifest(
            name="export_tool", version="1.0.0", description="Export",
            category="export", inputs=(), outputs=(),
        ))
        ingest = reg.filter_by_category("ingest")
        assert len(ingest) == 1
        assert ingest[0].name == "ingest_tool"

    def test_filter_by_capability(self):
        reg = ToolRegistry()
        reg.register(ToolManifest(
            name="searcher", version="1.0.0", description="Search",
            category="index", inputs=(), outputs=(),
            capabilities=("search", "keyword"),
        ))
        reg.register(ToolManifest(
            name="exporter", version="1.0.0", description="Export",
            category="export", inputs=(), outputs=(),
            capabilities=("export",),
        ))
        found = reg.filter_by_capability("search")
        assert len(found) == 1
        assert found[0].name == "searcher"

    def test_validate_dependencies_ok(self):
        reg = ToolRegistry()
        reg.register(self._make_manifest("base"))
        reg.register(self._make_manifest("child", deps=("base",)))
        errors = reg.validate_dependencies()
        assert errors == []

    def test_validate_dependencies_missing(self):
        reg = ToolRegistry()
        reg.register(self._make_manifest("orphan", deps=("missing_tool",)))
        errors = reg.validate_dependencies()
        assert len(errors) == 1
        assert "missing_tool" in errors[0]

    def test_detect_no_cycles(self):
        reg = ToolRegistry()
        reg.register(self._make_manifest("a"))
        reg.register(self._make_manifest("b", deps=("a",)))
        reg.register(self._make_manifest("c", deps=("b",)))
        assert reg.detect_cycles() == []

    def test_detect_cycle(self):
        reg = ToolRegistry()
        reg.register(self._make_manifest("x", deps=("z",)))
        reg.register(self._make_manifest("y", deps=("x",)))
        reg.register(self._make_manifest("z", deps=("y",)))
        cycles = reg.detect_cycles()
        assert len(cycles) > 0

    def test_execution_plan_simple(self):
        reg = ToolRegistry()
        reg.register(self._make_manifest("base"))
        reg.register(self._make_manifest("mid", deps=("base",)))
        reg.register(self._make_manifest("top", deps=("mid",)))
        plan = reg.execution_plan("top")
        assert plan == ["base", "mid", "top"]

    def test_execution_plan_unknown_target(self):
        reg = ToolRegistry()
        with pytest.raises(ValueError, match="Unknown tool"):
            reg.execution_plan("ghost")

    def test_execution_plan_cycle_raises(self):
        reg = ToolRegistry()
        reg.register(self._make_manifest("a", deps=("b",)))
        reg.register(self._make_manifest("b", deps=("a",)))
        with pytest.raises(ValueError, match="cycle"):
            reg.execution_plan("a")

    def test_export_json(self):
        reg = ToolRegistry()
        reg.register(self._make_manifest("tool_one"))
        exported = reg.export_json()
        data = json.loads(exported)
        assert data["schema_version"] == "1.0"
        assert data["tool_count"] == 1
        assert "tool_one" in data["tools"]

    def test_save(self, tmp_path):
        reg = ToolRegistry()
        reg.register(self._make_manifest("saved_tool"))
        path = str(tmp_path / "registry.json")
        file_hash = reg.save(path)
        assert Path(path).exists()
        assert len(file_hash) == 64
        content = Path(path).read_text(encoding="utf-8")
        recomputed = hashlib.sha256(content.encode("utf-8")).hexdigest()
        assert recomputed == file_hash


# ---------------------------------------------------------------------------
# BWC pipeline registry tests
# ---------------------------------------------------------------------------

class TestBWCRegistry:
    def test_build_registers_all_tools(self):
        reg = build_bwc_registry()
        assert reg.tool_count == 7

    def test_expected_tools_present(self):
        reg = build_bwc_registry()
        expected = [
            "integrity_ledger",
            "batch_ingest",
            "normalization_pipeline",
            "evidence_indexer",
            "chat_grounding",
            "legal_analysis",
            "bwc_export",
        ]
        for name in expected:
            assert reg.get(name) is not None, f"Missing tool: {name}"

    def test_all_dependencies_satisfied(self):
        reg = build_bwc_registry()
        errors = reg.validate_dependencies()
        assert errors == [], f"Dependency errors: {errors}"

    def test_no_cycles(self):
        reg = build_bwc_registry()
        cycles = reg.detect_cycles()
        assert cycles == [], f"Cycles detected: {cycles}"

    def test_export_execution_plan(self):
        reg = build_bwc_registry()
        plan = reg.execution_plan("bwc_export")
        # Ledger must come before everything
        assert plan.index("integrity_ledger") < plan.index("bwc_export")
        assert plan.index("batch_ingest") < plan.index("bwc_export")
        assert plan[-1] == "bwc_export"

    def test_chat_depends_on_indexer(self):
        reg = build_bwc_registry()
        plan = reg.execution_plan("chat_grounding")
        assert "evidence_indexer" in plan
        assert plan.index("evidence_indexer") < plan.index("chat_grounding")

    def test_each_tool_has_description(self):
        reg = build_bwc_registry()
        for tool in reg.list_all():
            assert len(tool.description) > 20

    def test_each_tool_has_version(self):
        reg = build_bwc_registry()
        for tool in reg.list_all():
            assert tool.version == "1.0.0"

    def test_categories_correct(self):
        reg = build_bwc_registry()
        categories = {t.name: t.category for t in reg.list_all()}
        assert categories["batch_ingest"] == "ingest"
        assert categories["normalization_pipeline"] == "normalize"
        assert categories["evidence_indexer"] == "index"
        assert categories["chat_grounding"] == "chat"
        assert categories["legal_analysis"] == "legal"
        assert categories["bwc_export"] == "export"

    def test_only_chat_is_nondeterministic(self):
        reg = build_bwc_registry()
        for tool in reg.list_all():
            if tool.name == "chat_grounding":
                assert tool.deterministic is False
            else:
                assert tool.deterministic is True, (
                    f"{tool.name} should be deterministic"
                )

    def test_export_json_valid(self):
        reg = build_bwc_registry()
        exported = reg.export_json()
        data = json.loads(exported)
        assert data["tool_count"] == 7
        assert len(data["tools"]) == 7

    def test_save_and_reload(self, tmp_path):
        reg = build_bwc_registry()
        path = str(tmp_path / "bwc_tools.json")
        reg.save(path)
        content = json.loads(Path(path).read_text(encoding="utf-8"))
        assert content["tool_count"] == 7
        assert "integrity_ledger" in content["tools"]
        assert "bwc_export" in content["tools"]
