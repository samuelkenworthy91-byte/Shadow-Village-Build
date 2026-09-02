"""Restore only a key matching the installed v35 APK. Never generate a replacement."""
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
    raise SystemExit('Compatible APK blocked: the previous build did not retain its signing key. Restore the original v35 keystore through KAGE_LIFE_KEYSTORE_BASE64; generating a new key would prevent an in-place update.')
certificate = subprocess.check_output(['keytool', '-exportcert', '-keystore', str(path), '-storepass', 'android', '-alias', 'androiddebugkey'])
if hashlib.sha256(certificate).hexdigest() != '8d0a35e037fecaa81a1ec58b13064d8feb575b987b42eb765e4fd8cde9d75dd6':
    raise SystemExit('Compatible APK blocked: this signing key does not match the last delivered v35 APK.')
print('Original v35 signing key verified; APK update can proceed')
