"""
Top-level conftest. Its only job is to put llm-scraper/ on sys.path so the
test modules under tests/ can `import normalize`, `import diff`, `import run`,
and `from scrapers import ...` exactly the same way the orchestrator does at
runtime. Putting this file at the project root also pins pytest's rootdir to
llm-scraper/, which is what we want.
"""

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
