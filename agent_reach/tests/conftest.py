# -*- coding: utf-8 -*-
"""Test setup. Runs offline. Works whatever the project folder is called."""
import importlib.util
import os
import pathlib
import sys
import tempfile

os.environ["AGENT_REACH_DISCOVERY_DB"] = os.path.join(tempfile.mkdtemp(), "test.db")
for key in ("LLM_PROVIDER", "LLM_API_KEY", "GROQ_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY",
            "ANTHROPIC_API_KEY", "AGENT_REACH_API_KEY"):
    os.environ.pop(key, None)

ROOT = pathlib.Path(__file__).resolve().parent.parent
if importlib.util.find_spec("agent_reach") is None:
    spec = importlib.util.spec_from_file_location(
        "agent_reach", ROOT / "__init__.py", submodule_search_locations=[str(ROOT)]
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["agent_reach"] = module
    spec.loader.exec_module(module)
