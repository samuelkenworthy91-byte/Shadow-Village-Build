"""Apply the reviewed gameplay update after portrait QC v33.

Strict input/output hashes prevent silently losing newer changes. The source
snapshot and original summon artwork are preserved in this repository.
"""
from pathlib import Path
import hashlib,json,shutil,subprocess
ROOT=Path(__file__).resolve().parents[1]
APP=ROOT/'app'
manifest=json.loads((ROOT/'overrides/gameplay_v34_files.json').read_text())
def digest(path):
 return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None
if not all(digest(APP/f)==m['after'] for f,m in manifest.items()):
 wrong=[f for f,m in manifest.items() if digest(APP/f)!=m['before']]
 if wrong: raise SystemExit('v34 input changed; reconcile instead of overwriting: '+', '.join(wrong))
 patch=(ROOT/'overrides/gameplay_v34.patch').read_bytes()
 args=['patch','-p1','--forward','--batch','--fuzz=0']
 subprocess.run(args+['--dry-run'],cwd=APP,input=patch,check=True,stdout=subprocess.DEVNULL)
 subprocess.run(args,cwd=APP,input=patch,check=True,stdout=subprocess.DEVNULL)
for f,m in manifest.items():
 if digest(APP/f)!=m['after']:raise SystemExit('v34 output mismatch: '+f)
art=ROOT/'summon_assets_v18';dest=APP/'public/summons';dest.mkdir(exist_ok=True)
files=sorted(art.glob('*.png'))
if len(files)!=10:raise SystemExit('Expected ten original summon images')
for src in files:shutil.copy2(src,dest/src.name)
print('v34 applied: names, recruitment balance, three clans, DoT, bloodlines and ten summons')
