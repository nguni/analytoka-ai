import sys
from pathlib import Path

# Add the project root to Python's import path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from app.tools import calculator

result = calculator(157, 38, "multiply")

print("Calculator result:", result)