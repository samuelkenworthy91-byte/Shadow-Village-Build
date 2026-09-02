"""Verify APK identity and honestly report compatibility with the last main build."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import zipfile

old = Path('previous-apk/app-debug.apk')
new = Path('app/android/app/build/outputs/apk/debug/app-debug.apk')
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
for key in ['package', 'origin', 'appId']:
    assert before[key] == after[key], f'Incompatible update: {key}'
assert after['package'] == 'com.shadowvillage.game.progression'
assert after['origin'] == ['https', 'localhost', None]
assert after['versionCode'] > before['versionCode'], 'Android versionCode must increase'
expected_certificate = Path('upgrade-results/signing-certificate.sha256').read_text().strip()
assert after['certificate'] == expected_certificate, 'APK did not use the retained signing key'
compatible = before['certificate'] == after['certificate']
if not compatible and os.environ.get('ALLOW_NEW_SIGNING_KEY') != 'true':
    raise SystemExit('Signing identity changed unexpectedly; refusing to publish')
Path('upgrade-results').mkdir(exist_ok=True)
Path('upgrade-results/apk-update-compatibility.json').write_text(json.dumps(dict(previous=before, update=after, apkVerified=True, saveFormatCompatible=True, inPlaceUpdateCompatible=compatible), indent=2) + '\n')
print('PASS: APK signature, retained signing key, package ID, save origin and increasing versionCode')
if not compatible:
    print('NOTICE: authorised build uses a new signing key; it cannot update the previous APK in place.')
print(f"Android versionCode {before['versionCode']} -> {after['versionCode']}")
