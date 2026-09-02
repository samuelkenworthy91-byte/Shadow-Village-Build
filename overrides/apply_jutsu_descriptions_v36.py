"""Apply display-only jutsu details; preserve v35 save, battle and progression data."""
from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / 'app'
manifest = json.loads((ROOT / 'overrides/jutsu_descriptions_v36_files.json').read_text())

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None

for name, expected in manifest['unchanged'].items():
    if digest(APP / name) != expected:
        raise SystemExit('v36 compatibility baseline changed: ' + name)
files = manifest['files']
if not all(digest(APP / name) == hashes['after'] for name, hashes in files.items()):
    wrong = [name for name, hashes in files.items() if digest(APP / name) != hashes['before']]
    if wrong:
        raise SystemExit('v36 input changed; reconcile before applying: ' + ', '.join(wrong))
    patch = (ROOT / 'overrides/jutsu_descriptions_v36.patch').read_bytes()
    args = ['patch', '-p1', '--forward', '--batch', '--fuzz=0']
    subprocess.run(args + ['--dry-run'], cwd=APP, input=patch, check=True, stdout=subprocess.DEVNULL)
    subprocess.run(args, cwd=APP, input=patch, check=True, stdout=subprocess.DEVNULL)
for name, hashes in files.items():
    if digest(APP / name) != hashes['after']:
        raise SystemExit('v36 output mismatch: ' + name)
print('v36: jutsu mechanics and flavour installed; save format, combat, catalogue IDs and app identity unchanged')
