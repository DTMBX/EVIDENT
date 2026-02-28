"""
B30 Phase 8 — Tool Manifest & Registry
========================================
Provides a typed manifest schema and a registry for BWC pipeline tools.

Each tool in the B30 pipeline declares:
  - name, version, description
  - inputs and outputs (typed schemas)
  - dependencies on other tools
  - integrity constraints (determinism, audit requirements)
  - capabilities (what the tool can do)

The registry enables:
  - Tool discovery (list, filter by capability)
  - Dependency validation (all deps registered before execution)
  - Pipeline composition (build ordered execution plans)
  - Manifest export (JSON for external systems)

Design constraints:
  - Manifests are immutable once registered
  - Tool names are unique within the registry
  - Dependency cycles are detected and rejected
  - All manifests are serializable to JSON
"""

import json
import hashlib
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Tool manifest schema
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ToolParam:
    """Describes a single input or output parameter."""
    name: str
    param_type: str  # "string", "file", "list", "dict", "bool", "int"
    required: bool = True
    description: str = ""
    default: Any = None


@dataclass(frozen=True)
class ToolManifest:
    """
    Immutable descriptor for a single BWC pipeline tool.

    Each manifest is a self-describing record of what a tool does,
    what it needs, and what guarantees it provides.
    """
    name: str
    version: str
    description: str
    category: str  # "ingest", "normalize", "index", "search", "chat", "legal", "export"
    inputs: tuple  # Tuple[ToolParam, ...]
    outputs: tuple  # Tuple[ToolParam, ...]
    dependencies: tuple = ()  # Tuple[str, ...] — names of required tools
    capabilities: tuple = ()  # Tuple[str, ...] — capability tags
    deterministic: bool = True
    requires_audit: bool = True
    author: str = "Evident Technologies"

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a JSON-safe dictionary."""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "category": self.category,
            "inputs": [
                {
                    "name": p.name,
                    "type": p.param_type,
                    "required": p.required,
                    "description": p.description,
                }
                for p in self.inputs
            ],
            "outputs": [
                {
                    "name": p.name,
                    "type": p.param_type,
                    "required": p.required,
                    "description": p.description,
                }
                for p in self.outputs
            ],
            "dependencies": list(self.dependencies),
            "capabilities": list(self.capabilities),
            "deterministic": self.deterministic,
            "requires_audit": self.requires_audit,
            "author": self.author,
        }

    @property
    def manifest_hash(self) -> str:
        """SHA-256 of the canonical JSON representation."""
        canonical = json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Tool registry
# ---------------------------------------------------------------------------

class ToolRegistry:
    """
    In-memory registry of BWC pipeline tools.

    Supports:
      - Registration with uniqueness enforcement
      - Discovery by name or capability
      - Dependency validation (no missing deps, no cycles)
      - Pipeline plan generation (topological order)
      - JSON export for external systems
    """

    def __init__(self):
        self._tools: Dict[str, ToolManifest] = {}

    @property
    def tool_names(self) -> List[str]:
        return sorted(self._tools.keys())

    @property
    def tool_count(self) -> int:
        return len(self._tools)

    def register(self, manifest: ToolManifest) -> None:
        """
        Register a tool manifest.

        Raises ValueError if a tool with the same name is already registered.
        """
        if manifest.name in self._tools:
            raise ValueError(f"Tool already registered: {manifest.name}")
        self._tools[manifest.name] = manifest
        logger.info("Registered tool: %s v%s", manifest.name, manifest.version)

    def get(self, name: str) -> Optional[ToolManifest]:
        """Retrieve a manifest by tool name."""
        return self._tools.get(name)

    def list_all(self) -> List[ToolManifest]:
        """List all registered manifests in sorted order."""
        return [self._tools[n] for n in sorted(self._tools)]

    def filter_by_category(self, category: str) -> List[ToolManifest]:
        """Filter manifests by category."""
        return [m for m in self._tools.values() if m.category == category]

    def filter_by_capability(self, capability: str) -> List[ToolManifest]:
        """Filter manifests by capability tag."""
        return [m for m in self._tools.values() if capability in m.capabilities]

    def validate_dependencies(self) -> List[str]:
        """
        Validate that all declared dependencies are registered.

        Returns a list of error messages. Empty list means valid.
        """
        errors = []
        for name, manifest in self._tools.items():
            for dep in manifest.dependencies:
                if dep not in self._tools:
                    errors.append(
                        f"Tool '{name}' depends on '{dep}', which is not registered."
                    )
        return errors

    def detect_cycles(self) -> List[List[str]]:
        """
        Detect dependency cycles using DFS.

        Returns a list of cycle paths. Empty list means no cycles.
        """
        cycles = []
        visited: Set[str] = set()
        path: List[str] = []
        on_path: Set[str] = set()

        def dfs(name: str):
            if name in on_path:
                cycle_start = path.index(name)
                cycles.append(path[cycle_start:] + [name])
                return
            if name in visited:
                return
            visited.add(name)
            on_path.add(name)
            path.append(name)

            manifest = self._tools.get(name)
            if manifest:
                for dep in manifest.dependencies:
                    if dep in self._tools:
                        dfs(dep)

            path.pop()
            on_path.remove(name)

        for tool_name in self._tools:
            dfs(tool_name)

        return cycles

    def execution_plan(self, target: str) -> List[str]:
        """
        Generate a topological execution order to run the given target tool.

        Returns an ordered list of tool names. The target tool is last.
        Raises ValueError if the target is unknown or has a dependency cycle.
        """
        if target not in self._tools:
            raise ValueError(f"Unknown tool: {target}")

        order: List[str] = []
        visited: Set[str] = set()
        temp: Set[str] = set()

        def visit(name: str):
            if name in temp:
                raise ValueError(f"Dependency cycle detected involving '{name}'")
            if name in visited:
                return
            temp.add(name)
            manifest = self._tools.get(name)
            if manifest:
                for dep in manifest.dependencies:
                    if dep in self._tools:
                        visit(dep)
            temp.remove(name)
            visited.add(name)
            order.append(name)

        visit(target)
        return order

    def export_json(self, indent: int = 2) -> str:
        """Export the full registry as JSON."""
        registry_dict = {
            "schema_version": "1.0",
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "tool_count": self.tool_count,
            "tools": {
                name: manifest.to_dict()
                for name, manifest in sorted(self._tools.items())
            },
        }
        return json.dumps(registry_dict, indent=indent, sort_keys=True)

    def save(self, path: str) -> str:
        """Save registry to a JSON file. Returns the file hash."""
        content = self.export_json()
        filepath = Path(path)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(content, encoding="utf-8")
        return hashlib.sha256(content.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# B30 BWC Pipeline Tool Definitions
# ---------------------------------------------------------------------------

def build_bwc_registry() -> ToolRegistry:
    """
    Build and return the complete B30 BWC pipeline tool registry.

    Registers all seven pipeline stages with their manifests.
    """
    registry = ToolRegistry()

    # --- 1. Integrity Ledger ---
    registry.register(ToolManifest(
        name="integrity_ledger",
        version="1.0.0",
        description=(
            "Append-only JSONL ledger with SHA-256 hash chain. "
            "Provides tamper-evident audit trail independent of the database."
        ),
        category="audit",
        inputs=(
            ToolParam("action", "string", description="Action label"),
            ToolParam("evidence_id", "string", required=False, description="Evidence UUID"),
            ToolParam("sha256", "string", required=False, description="Hash of artifact"),
            ToolParam("actor", "string", required=False, description="Who performed the action"),
            ToolParam("details", "dict", required=False, description="Arbitrary metadata"),
        ),
        outputs=(
            ToolParam("entry", "dict", description="Ledger entry with seq, hashes, timestamp"),
        ),
        dependencies=(),
        capabilities=("audit", "hash-chain", "tamper-detection", "append-only"),
        deterministic=True,
        requires_audit=False,  # It IS the audit
    ))

    # --- 2. Batch Ingest ---
    registry.register(ToolManifest(
        name="batch_ingest",
        version="1.0.0",
        description=(
            "Folder-based batch ingest with BWC filename parsing, "
            "sequence grouping, and duplicate detection."
        ),
        category="ingest",
        inputs=(
            ToolParam("folder_path", "string", description="Path to folder of evidence files"),
            ToolParam("case_ref", "string", required=False, description="Case reference label"),
            ToolParam("actor", "string", required=False, description="Ingesting user/system"),
        ),
        outputs=(
            ToolParam("manifest", "dict", description="Ingest manifest with file list, groups, hashes"),
            ToolParam("sequence_groups", "list", description="Auto-detected BWC sequence groups"),
        ),
        dependencies=("integrity_ledger",),
        capabilities=("ingest", "bwc-parsing", "duplicate-detection", "sequence-grouping"),
        deterministic=True,
        requires_audit=True,
    ))

    # --- 3. Normalization Pipeline ---
    registry.register(ToolManifest(
        name="normalization_pipeline",
        version="1.0.0",
        description=(
            "Generates derivative artifacts (thumbnails, proxies, waveforms, "
            "text extractions) from ingested evidence by MIME type."
        ),
        category="normalize",
        inputs=(
            ToolParam("evidence_id", "string", description="Evidence UUID"),
            ToolParam("original_path", "file", description="Path to original file"),
            ToolParam("mime_type", "string", description="MIME type of the original"),
        ),
        outputs=(
            ToolParam("derivatives", "list", description="List of generated derivative descriptors"),
            ToolParam("metadata", "dict", description="Extracted media metadata"),
        ),
        dependencies=("integrity_ledger",),
        capabilities=(
            "thumbnail", "proxy", "waveform", "metadata-extraction",
            "text-extraction", "video", "audio", "image", "document",
        ),
        deterministic=True,
        requires_audit=True,
    ))

    # --- 4. Evidence Indexer ---
    registry.register(ToolManifest(
        name="evidence_indexer",
        version="1.0.0",
        description=(
            "Filesystem-based search index supporting keyword, phrase, "
            "and AND queries. Persists to JSON for portability."
        ),
        category="index",
        inputs=(
            ToolParam("evidence_id", "string", description="Evidence UUID"),
            ToolParam("text_content", "string", description="Extracted text to index"),
            ToolParam("metadata", "dict", required=False, description="Additional metadata to index"),
        ),
        outputs=(
            ToolParam("indexed", "bool", description="Whether indexing succeeded"),
            ToolParam("entity_count", "int", description="Number of entities extracted"),
        ),
        dependencies=("integrity_ledger",),
        capabilities=("search", "keyword", "phrase", "entity-extraction", "persistence"),
        deterministic=True,
        requires_audit=True,
    ))

    # --- 5. Chat Grounding ---
    registry.register(ToolManifest(
        name="chat_grounding",
        version="1.0.0",
        description=(
            "Evidence-grounded chat assistant with mandatory citation rules, "
            "fabrication detection, and safe-mode gating."
        ),
        category="chat",
        inputs=(
            ToolParam("user_message", "string", description="User's question or request"),
            ToolParam("case_id", "string", required=False, description="Case scope for search"),
            ToolParam("safe_mode", "bool", required=False, description="Enable safe mode restrictions"),
        ),
        outputs=(
            ToolParam("response", "string", description="Grounded response with citations"),
            ToolParam("citations", "list", description="Validated citation references"),
            ToolParam("warnings", "list", description="Fabrication or quality warnings"),
        ),
        dependencies=("evidence_indexer", "integrity_ledger"),
        capabilities=(
            "chat", "citation-validation", "fabrication-detection",
            "tool-execution", "evidence-search", "safe-mode",
        ),
        deterministic=False,  # LLM responses are non-deterministic
        requires_audit=True,
    ))

    # --- 6. Legal Analysis ---
    registry.register(ToolManifest(
        name="legal_analysis",
        version="1.0.0",
        description=(
            "Structured legal research helpers: issue mapping, analysis templates, "
            "verified citation registry, and argument outline builder."
        ),
        category="legal",
        inputs=(
            ToolParam("evidence_id", "string", description="Evidence UUID"),
            ToolParam("text_content", "string", description="Text to analyze"),
            ToolParam("filename", "string", required=False, description="Original filename"),
        ),
        outputs=(
            ToolParam("issues", "list", description="Detected constitutional issues"),
            ToolParam("citations", "list", description="Verified legal citations"),
            ToolParam("argument_outline", "dict", description="Structured argument outline"),
        ),
        dependencies=("integrity_ledger",),
        capabilities=(
            "issue-mapping", "constitutional-analysis", "citation-verification",
            "argument-building", "template-generation",
        ),
        deterministic=True,
        requires_audit=True,
    ))

    # --- 7. BWC Export ---
    registry.register(ToolManifest(
        name="bwc_export",
        version="1.0.0",
        description=(
            "Court-ready ZIP packages with size tiers, deterministic naming, "
            "ledger extract, search index snapshot, and integrity report."
        ),
        category="export",
        inputs=(
            ToolParam("evidence_ids", "list", description="Evidence UUIDs to export"),
            ToolParam("case_ref", "string", description="Case reference for naming"),
            ToolParam("exported_by", "string", required=False, description="Exporting actor"),
        ),
        outputs=(
            ToolParam("export_path", "string", description="Path to the generated ZIP"),
            ToolParam("package_sha256", "string", description="SHA-256 of the package"),
            ToolParam("size_tier", "string", description="Size tier classification"),
            ToolParam("manifest", "dict", description="Package manifest"),
        ),
        dependencies=("integrity_ledger", "batch_ingest"),
        capabilities=(
            "export", "compression", "size-tier", "court-ready",
            "deterministic-naming", "integrity-report",
        ),
        deterministic=True,
        requires_audit=True,
    ))

    return registry
