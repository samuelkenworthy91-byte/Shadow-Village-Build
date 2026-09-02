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


def normalise_digest(value):
    return re.sub(r'[^0-9a-f]', '', value.lower())


def inspect(path):
    cert_run = subprocess.run(
        [str(build_tools / 'apksigner'), 'verify', '--print-certs', str(path)],
        text=True,
        capture_output=True,
        check=True,
    )
    certs = cert_run.stdout + '\n' + cert_run.stderr
    cert_match = re.search(
        r'(?:Signer\s*#?\s*1\s+)?certificate\s+SHA-?256\s+digest\s*:\s*([0-9A-Fa-f: ]+)',
        certs,
        re.IGNORECASE,
    )
    if not cert_match:
        raise SystemExit('Could not parse APK signing certificate from apksigner output:\n' + certs[:4000])
    certificate = normalise_digest(cert_match.group(1))
    if len(certificate) != 64:
        raise SystemExit(f'Unexpected SHA-256 certificate digest length ({len(certificate)}): {certificate}')

    badging = subprocess.check_output([str(build_tools / 'aapt'), 'dump', 'badging', str(path)], text=True)
    package = re.search(r"package: name='([^']+)' versionCode='(\d+)' versionName='([^']+)'", badging)
    if not package:
        raise SystemExit('Could not parse package/version information from aapt output')

    with zipfile.ZipFile(path) as apk:
        config = json.loads(apk.read('assets/capacitor.config.json'))
        server = config.get('server', {})
        origin = [server.get('androidScheme', 'https'), server.get('hostname', 'localhost'), server.get('url')]
        web = apk.read('assets/public/index.html').decode()
        assert 'shadow-village-save-v' in web, 'Save support absent'

    return dict(
        package=package[1],
        versionCode=int(package[2]),
        versionName=package[3],
        certificate=certificate,
        origin=origin,
        appId=config['appId'],
        sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
    )


before, after = inspect(old), inspect(new)
for key in ['package', 'origin', 'appId']:
    assert before[key] == after[key], f'Incompatible update: {key}'
assert after['package'] == 'com.shadowvillage.game.progression'
assert after['origin'] == ['https', 'localhost', None]
assert after['versionCode'] > before['versionCode'], 'Android versionCode must increase'
expected_certificate = normalise_digest(Path('upgrade-results/signing-certificate.sha256').read_text().strip())
assert after['certificate'] == expected_certificate, 'APK did not use the prepared signing key'
compatible = before['certificate'] == after['certificate']
if not compatible and os.environ.get('ALLOW_NEW_SIGNING_KEY') != 'true':
    raise SystemExit('Signing identity changed unexpectedly; refusing to publish')
Path('upgrade-results').mkdir(exist_ok=True)
Path('upgrade-results/apk-update-compatibility.json').write_text(
    json.dumps(
        dict(
            previous=before,
            update=after,
            apkVerified=True,
            saveFormatCompatible=True,
            inPlaceUpdateCompatible=compatible,
        ),
        indent=2,
    ) + '\n'
)
print('PASS: APK signature, package ID, save origin and increasing versionCode')
if compatible:
    print('PASS: signing certificate matches the previous APK; in-place Android update is compatible')
else:
    print('NOTICE: authorised build uses a new signing key; it cannot update the previous APK in place.')
print(f"Android versionCode {before['versionCode']} -> {after['versionCode']}")
