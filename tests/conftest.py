import sys
from pathlib import Path

# Add project root to sys.path so pytest can locate top-level packages
BASE_DIR = Path(__file__).parent.parent.resolve()
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
