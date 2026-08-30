"""Shared test configuration.

Modules in tests/ha_required/ import Home Assistant internals and can only run
in an environment with the HA test stack installed (pytest-homeassistant-
custom-component). If ``homeassistant`` is not importable here they are not
collected at all; the pure-logic tests always run.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

HA_AVAILABLE = importlib.util.find_spec("homeassistant") is not None

if not HA_AVAILABLE:
    collect_ignore = ["ha_required"]

    #: The real package __init__.py imports Home Assistant internals, which are
    #: not importable in this environment. Register a synthetic parent package
    #: that points at the real modules so the pure-logic modules (api, model)
    #: can still be imported and tested without executing __init__.py.
    import types

    _cc = types.ModuleType("custom_components")
    _cc.__path__ = [str(REPO_ROOT / "custom_components")]
    _cc.__package__ = "custom_components"
    sys.modules["custom_components"] = _cc

    _pkg = types.ModuleType("custom_components.ballinora_match_tracker")
    _pkg.__path__ = [str(REPO_ROOT / "custom_components" / "ballinora_match_tracker")]
    _pkg.__package__ = "custom_components.ballinora_match_tracker"
    sys.modules["custom_components.ballinora_match_tracker"] = _pkg
