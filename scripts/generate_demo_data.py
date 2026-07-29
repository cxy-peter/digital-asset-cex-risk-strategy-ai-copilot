import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))


from risk_copilot.runtime import RuntimeContext

root = PROJECT_ROOT
context = RuntimeContext.create(root)
for name, path in context.ensure_demo_data(force=True).items():
    print(name, path)
