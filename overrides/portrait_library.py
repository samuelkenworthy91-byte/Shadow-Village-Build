"""Shared portrait inventory for staged builds and final quality control."""
import argparse
import json
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
QC = json.loads((REPO / 'overrides/portrait_qc_v33.json').read_text())
APP = REPO / 'app'
OUT = APP / 'public/ninjas'


def approved_ids(max_id=370):
    return [i for i in QC['approved_ids'] if i <= max_id]


def prune():
    for key in QC['removed']:
        (OUT / f'ninja_{int(key):03d}.png').unlink(missing_ok=True)


def validate_assets(max_id=370):
    expected = set(approved_ids(max_id))
    actual = {int(p.stem.split('_')[1]) for p in OUT.glob('ninja_*.png')}
    if actual != expected:
        raise RuntimeError(f'Portrait inventory mismatch: missing={sorted(expected-actual)}, extra={sorted(actual-expected)}')
    print(f'Validated {len(actual)} approved portrait assets (IDs through {max_id})')


def install(max_id=370):
    OUT.mkdir(parents=True, exist_ok=True)
    for i in approved_ids(max_id):
        if i <= 80:
            continue  # Original PNGs come from the base archive.
        stem = f'ninja_{i:03d}'
        sources = [REPO / f'overrides/ninja_assets_v{v}/direct/{stem}.webp' for v in (29, 28, 27, 26)]
        src = next((p for p in sources if p.is_file()), None)
        if src is None:
            raise RuntimeError(f'Missing approved portrait source: {stem}')
        dims = subprocess.check_output(['identify', '-format', '%wx%h', str(src)], text=True)
        command = ['convert', str(src)]
        if dims != '240x536':
            command += ['-trim', '+repage', '-resize', '230x520>', '-gravity', 'south', '-background', 'none', '-extent', '240x536']
        subprocess.run(command + [f'PNG32:{OUT / (stem + ".png")}'], check=True)
    prune()
    validate_assets(max_id)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['install', 'validate'])
    parser.add_argument('--max-id', type=int, default=370)
    args = parser.parse_args()
    (install if args.action == 'install' else validate_assets)(args.max_id)
