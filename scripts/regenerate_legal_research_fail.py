import py_compile
import json
from pathlib import Path

files = [
    r"C:\web-dev\github-repos\Evident\backend\src\legal_research_integration.py",
    r"C:\web-dev\github-repos\Evident\backend\app\root_legacy\legal_research_integration.py",
]

results = []
for f in files:
    try:
        py_compile.compile(f, doraise=True)
    except Exception as e:
        results.append({"path": str(Path(f).resolve()), "error": f"Sorry: {type(e).__name__}: {e}"})

Path(r"_legal_research_fail.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
print(json.dumps(results, indent=2))
