"""Reuse the cached signing key; allow the user-authorised one-time v36 bootstrap."""
import base64
import hashlib
import os
from pathlib import Path
import subprocess

path = Path.home() / '.android/debug.keystore'
encoded = os.environ.get('KAGE_LIFE_KEYSTORE_BASE64', '')
if encoded:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(base64.b64decode(encoded, validate=True))
    path.chmod(0o600)
if not path.is_file():
    if os.environ.get('ALLOW_NEW_SIGNING_KEY') != 'true':
        raise SystemExit('Signing key unavailable: restore KAGE_LIFE_KEYSTORE_BASE64. Refusing to silently change the signing identity.')
    path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(['keytool', '-genkeypair', '-keystore', str(path), '-storepass', 'android',
        '-keypass', 'android', '-alias', 'androiddebugkey', '-keyalg', 'RSA', '-keysize', '2048',
        '-validity', '10000', '-dname', 'CN=Kage Life Debug,O=Kage Life,C=GB'], check=True)
    path.chmod(0o600)
certificate = subprocess.check_output(['keytool', '-exportcert', '-keystore', str(path), '-storepass', 'android', '-alias', 'androiddebugkey'])
Path('upgrade-results').mkdir(exist_ok=True)
Path('upgrade-results/signing-certificate.sha256').write_text(hashlib.sha256(certificate).hexdigest() + '\n')
print('Build signing key prepared at the explicit cached path')
