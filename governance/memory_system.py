"""
MEMORY & STATE MANAGEMENT SYSTEM
Tracks architecture decisions, patterns, and learnings across all platforms
Enables progressive intelligence and consistent design patterns
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum


class ComponentType(Enum):
    """Types of UI components we build"""
    WEB_REACT = "web_react"
    WEB_COMPONENT = "web_component"
    MOBILE_FLUTTER = "mobile_flutter"
    MOBILE_NATIVE_IOS = "mobile_native_ios"
    MOBILE_NATIVE_ANDROID = "mobile_native_android"
    DESKTOP_ELECTRON = "desktop_electron"
    DESKTOP_WPFNET = "desktop_wpfnet"  # Windows Forms/.NET


class Platform(Enum):
    """Target platforms"""
    WEB = "web"
    MOBILE = "mobile"
    WINDOWS = "windows"
    ALL = "all"


@dataclass
class DesignToken:
    """Design system token (color, spacing, typography, etc.)"""
    name: str
    value: str
    category: str  # color, spacing, typography, effect
    platform: str  # web, mobile, windows, all
    usage: str  # Where it's used
    created_date: str = None
    
    def __post_init__(self):
        if not self.created_date:
            self.created_date = datetime.now().isoformat()


@dataclass
class ComponentPattern:
    """Reusable component pattern across platforms"""
    name: str
    description: str
    platforms_implemented: List[str]  # web, mobile, windows
    component_type: str
    props_interface: Dict[str, str]  # prop_name -> type
    state_interface: Dict[str, str]
    events_emitted: List[str]
    created_date: str = None
    last_updated: str = None
    
    def __post_init__(self):
        if not self.created_date:
            self.created_date = datetime.now().isoformat()
        if not self.last_updated:
            self.last_updated = datetime.now().isoformat()


@dataclass
class ArchitectureDecision:
    """Record of important architecture decisions"""
    decision_id: str
    title: str
    context: str  # Why this decision
    decision: str  # What was decided
    rationale: str  # Why this way
    alternatives_considered: List[str]
    platforms_affected: List[str]
    status: str  # active, deprecated, under_review
    date_made: str = None
    
    def __post_init__(self):
        if not self.date_made:
            self.date_made = datetime.now().isoformat()


@dataclass
class Implementation:
    """Track each UI implementation"""
    impl_id: str
    component_name: str
    platform: str  # web, mobile, windows
    file_path: str
    lines_of_code: int
    complexity: str  # simple, medium, complex
    dependencies: List[str]
    tests_included: bool
    screenshots_included: bool
    created_date: str = None
    status: str = "in_progress"  # in_progress, complete, under_review
    notes: str = ""
    
    def __post_init__(self):
        if not self.created_date:
            self.created_date = datetime.now().isoformat()


class MemorySystem:
    """Central memory system that learns from each implementation"""
    
    def __init__(self, memory_dir: Path = Path("./governance/memories")):
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        
        self.design_tokens: Dict[str, DesignToken] = {}
        self.component_patterns: Dict[str, ComponentPattern] = {}
        self.architecture_decisions: Dict[str, ArchitectureDecision] = {}
        self.implementations: List[Implementation] = []
        self.learnings: List[Dict[str, Any]] = []
        
        self.load_all()
    
    def add_design_token(self, token: DesignToken):
        """Add a design system token"""
        self.design_tokens[token.name] = token
        self._save_tokens()
    
    def add_component_pattern(self, pattern: ComponentPattern):
        """Add a reusable component pattern"""
        self.component_patterns[pattern.name] = pattern
        self._save_patterns()
    
    def add_architecture_decision(self, decision: ArchitectureDecision):
        """Record an architecture decision"""
        self.architecture_decisions[decision.decision_id] = decision
        self._save_decisions()
    
    def record_implementation(self, impl: Implementation):
        """Record a completed implementation"""
        self.implementations.append(impl)
        self._save_implementations()
    
    def add_learning(self, learning: Dict[str, Any]):
        """Add a learning from implementation"""
        learning['recorded_date'] = datetime.now().isoformat()
        self.learnings.append(learning)
        self._save_learnings()
    
    def get_pattern_for_platform(self, pattern_name: str, platform: str) -> Optional[ComponentPattern]:
        """Get a component pattern implementation for specific platform"""
        pattern = self.component_patterns.get(pattern_name)
        if pattern and platform in pattern.platforms_implemented:
            return pattern
        return None
    
    def get_design_tokens_for_platform(self, platform: str) -> List[DesignToken]:
        """Get all design tokens for a specific platform"""
        return [
            token for token in self.design_tokens.values()
            if token.platform == platform or token.platform == 'all'
        ]
    
    def get_completed_implementations(self) -> List[Implementation]:
        """Get all completed implementations"""
        return [impl for impl in self.implementations if impl.status == 'complete']
    
    def get_learnings_for_pattern(self, pattern_name: str) -> List[Dict[str, Any]]:
        """Get all learnings related to a pattern"""
        return [l for l in self.learnings if pattern_name in l.get('tags', [])]
    
    def _save_tokens(self):
        """Save design tokens to file"""
        path = self.memory_dir / "design_tokens.json"
        data = {name: asdict(token) for name, token in self.design_tokens.items()}
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _save_patterns(self):
        """Save component patterns to file"""
        path = self.memory_dir / "component_patterns.json"
        data = {name: asdict(pattern) for name, pattern in self.component_patterns.items()}
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _save_decisions(self):
        """Save architecture decisions to file"""
        path = self.memory_dir / "architecture_decisions.json"
        data = {did: asdict(decision) for did, decision in self.architecture_decisions.items()}
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _save_implementations(self):
        """Save implementations to file"""
        path = self.memory_dir / "implementations.json"
        data = [asdict(impl) for impl in self.implementations]
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _save_learnings(self):
        """Save learnings to file"""
        path = self.memory_dir / "learnings.json"
        with open(path, 'w') as f:
            json.dump(self.learnings, f, indent=2)
    
    def load_all(self):
        """Load all memories from disk"""
        # Load design tokens
        tokens_file = self.memory_dir / "design_tokens.json"
        if tokens_file.exists():
            with open(tokens_file) as f:
                data = json.load(f)
                self.design_tokens = {
                    name: DesignToken(**token_data)
                    for name, token_data in data.items()
                }
        
        # Load component patterns
        patterns_file = self.memory_dir / "component_patterns.json"
        if patterns_file.exists():
            with open(patterns_file) as f:
                data = json.load(f)
                self.component_patterns = {
                    name: ComponentPattern(**pattern_data)
                    for name, pattern_data in data.items()
                }
        
        # Load architecture decisions
        decisions_file = self.memory_dir / "architecture_decisions.json"
        if decisions_file.exists():
            with open(decisions_file) as f:
                data = json.load(f)
                self.architecture_decisions = {
                    did: ArchitectureDecision(**decision_data)
                    for did, decision_data in data.items()
                }
        
        # Load implementations
        impl_file = self.memory_dir / "implementations.json"
        if impl_file.exists():
            with open(impl_file) as f:
                data = json.load(f)
                self.implementations = [Implementation(**impl_data) for impl_data in data]
        
        # Load learnings
        learnings_file = self.memory_dir / "learnings.json"
        if learnings_file.exists():
            with open(learnings_file) as f:
                self.learnings = json.load(f)


# ======================== DESIGN SYSTEM (EVIDENT BRANDING) ========================

def initialize_design_system() -> MemorySystem:
    """Initialize design system with Evident brand tokens"""
    memory = MemorySystem()
    
    # Only add if not already present
    if 'primary-blue' not in memory.design_tokens:
        # Colors
        memory.add_design_token(DesignToken(
            name='primary-blue',
            value='#0b73d2',
            category='color',
            platform='all',
            usage='Primary actions, headers, key UI elements'
        ))
        
        memory.add_design_token(DesignToken(
            name='accent-orange',
            value='#e07a5f',
            category='color',
            platform='all',
            usage='Highlights, alerts, secondary actions'
        ))
        
        memory.add_design_token(DesignToken(
            name='neutral-gray',
            value='#f6f7f9',
            category='color',
            platform='all',
            usage='Backgrounds, borders, disabled states'
        ))
        
        memory.add_design_token(DesignToken(
            name='text-dark',
            value='#1a1a1a',
            category='color',
            platform='all',
            usage='Primary text'
        ))
        
        # Spacing
        memory.add_design_token(DesignToken(
            name='spacing-xs',
            value='4px',
            category='spacing',
            platform='all',
            usage='Minimal spacing'
        ))
        
        memory.add_design_token(DesignToken(
            name='spacing-sm',
            value='8px',
            category='spacing',
            platform='all',
            usage='Small spacing'
        ))
        
        memory.add_design_token(DesignToken(
            name='spacing-md',
            value='16px',
            category='spacing',
            platform='all',
            usage='Standard spacing'
        ))
        
        memory.add_design_token(DesignToken(
            name='spacing-lg',
            value='24px',
            category='spacing',
            platform='all',
            usage='Large spacing'
        ))
        
        # Typography
        memory.add_design_token(DesignToken(
            name='font-family-sans',
            value='-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
            category='typography',
            platform='all',
            usage='Main font family'
        ))
        
        memory.add_design_token(DesignToken(
            name='font-size-body',
            value='14px',
            category='typography',
            platform='all',
            usage='Body text'
        ))
        
        memory.add_design_token(DesignToken(
            name='font-size-heading',
            value='20px',
            category='typography',
            platform='all',
            usage='Headings'
        ))
    
    return memory


if __name__ == '__main__':
    memory = initialize_design_system()
    print(f"✓ Memory system initialized")
    print(f"✓ Design tokens: {len(memory.design_tokens)}")
    print(f"✓ Component patterns: {len(memory.component_patterns)}")
