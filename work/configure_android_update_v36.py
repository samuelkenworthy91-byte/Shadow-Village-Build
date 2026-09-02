"""Version each rebuilt APK while retaining the existing application identity."""
import os
from pathlib import Path
import re

path = Path('app/android/app/build.gradle')
source = path.read_text()
assert 'com.shadowvillage.game.progression' in source, 'Application ID changed'
run = int(os.environ['GITHUB_RUN_NUMBER'])
assert 0 < run < 2_000_000_000
source, count = re.subn(r'\bversionCode\s+\d+', f'versionCode {1000 + run}', source)
assert count == 1
source, count = re.subn(r'\bversionName\s+"[^"]+"', f'versionName "0.36.{run}"', source)
assert count == 1
# Explicitly select the retained key; never let Gradle generate another identity.
assert source.count('    buildTypes {') == 1
source = source.replace('    buildTypes {', '    signingConfigs {\n        debug {\n            storeFile file(System.getProperty("user.home") + "/.android/debug.keystore")\n            storePassword "android"\n            keyAlias "androiddebugkey"\n            keyPassword "android"\n        }\n    }\n    buildTypes {')
path.write_text(source)
print(f'Android update versionCode={1000 + run}, versionName=0.36.{run}')
