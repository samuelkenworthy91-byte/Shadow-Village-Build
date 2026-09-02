"""Reject APKs that cannot update the last delivered APK with its WebView saves."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import zipfile

old = Path('previous-apk/app-debug.apk')
new = Path('app/android/app/build/outputs/apk/debug/app-debug.apk')
assert hashlib.sha256(old.read_bytes()).hexdigest() == '1a49251639aca07020239647acaf61725876628226c6761d4ad9d721b6991f0e', 'Wrong baseline APK'
root = Path(os.environ['ANDROID_HOME']) / 'build-tools'
build_tools = sorted((p for p in root.iterdir() if (p / 'apksigner').exists()), key=lambda p: tuple(int(x) for x in re.findall(r'\d+', p.name)))[-1]

def inspect(path):
    certs = subprocess.check_output([str(build_tools / 'apksigner'), 'verify', '--print-certs', str(path)], text=True)
    certificate = re.search(r'Signer #1 certificate SHA-256 digest: (\w+)', certs).group(1)
    badging = subprocess.check_output([str(build_tools / 'aapt'), 'dump', 'badging', str(path)], text=True)
    package = re.search(r"package: name='([^']+)' versionCode='(\d+)' versionName='([^']+)'", badging)
    with zipfile.ZipFile(path) as apk:
        config = json.loads(apk.read('assets/capacitor.config.json'))
        server = config.get('server', {})
        origin = [server.get('androidScheme', 'https'), server.get('hostname', 'localhost'), server.get('url')]
        web = apk.read('assets/public/index.html').decode()
        assert 'shadow-village-save-v' in web, 'Save support absent'
    return dict(package=package[1], versionCode=int(package[2]), versionName=package[3], certificate=certificate, origin=origin, appId=config['appId'], sha256=hashlib.sha256(path.read_bytes()).hexdigest())

before, after = inspect(old), inspect(new)
for key in ['certificate', 'package', 'origin', 'appId']:
    assert before[key] == after[key], f'Incompatible update: {key}'
assert after['package'] == 'com.shadowvillage.game.progression'
assert after['origin'] == ['https', 'localhost', None]
assert after['versionCode'] > before['versionCode'], 'Android versionCode must increase'
Path('upgrade-results').mkdir(exist_ok=True)
Path('upgrade-results/apk-update-compatibility.json').write_text(json.dumps(dict(previous=before, update=after, result='PASS'), indent=2) + '\n')
print('PASS: same signing certificate, package ID, WebView save origin; increased versionCode')
print(f"Android versionCode {before['versionCode']} -> {after['versionCode']}")
