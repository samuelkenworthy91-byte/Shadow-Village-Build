from pathlib import Path
import subprocess
import sys

script = Path(__file__).with_name("import_batch.py")
raise SystemExit(
    subprocess.call(
        [sys.executable, str(script), "--start", "1", "--end", "20", "--require-complete"]
    )
)
