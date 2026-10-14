from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"backend"))
from itpm.infrastructure.preview_entry import render_entry
