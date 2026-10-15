"""Reset the workshop: delete untracked and ignored files, keeping .env and .venv.

Run: uv run workshop/clean.py [--dry-run]
This also removes files you created or copied in, such as chapter work in .github/.
"""

import argparse
from pathlib import Path
import subprocess
import sys

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--dry-run", "-n", action="store_true", help="List what would be deleted")
args = parser.parse_args()
repo = Path(__file__).resolve().parents[1]
command = ["git", "-C", str(repo), "clean", "-ndx" if args.dry_run else "-fdx", "-e", ".env", "-e", ".venv"]
sys.exit(subprocess.run(command).returncode)
