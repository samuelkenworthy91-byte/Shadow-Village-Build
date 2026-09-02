# Android update compatibility

The v36 jutsu update preserves the v35 save parser, game catalogue and progression
IDs, application ID `com.shadowvillage.game.progression`, and WebView origin
`https://localhost`. All three `shadow-village-save-v3-slot-*` slots are tested.

## Existing signing-key blocker

The v34 and v35 APKs were signed with **different** temporary debug certificates:

| Build | Certificate SHA-256 | Created (UTC) |
| --- | --- | --- |
| v34 | `fce9f9f5af04874fb420d2a48e1ddf83e46110b13d4ab7177c4dc29fa759d361` | 2026-09-02 14:55:29 |
| v35 | `8d0a35e037fecaa81a1ec58b13064d8feb575b987b42eb765e4fd8cde9d75dd6` | 2026-09-02 15:16:07 |

These fingerprints were read from the actual APK v2 signing blocks. In v35 build
run `33647060245`, the cache restore reported no signing-key cache. Its final
cache-save step reported that the configured path did not exist. Neither APK
artifact nor the source artifact contains the private signing key.

A new key cannot create an ordinary Android update for either installed APK.
Do not uninstall the existing game or publish a replacement as update-compatible.
The pipeline verifies all game/UI changes before stopping at this blocker.

## Restoring a matching key

If the original v35 debug keystore exists in an external backup, store its Base64
contents in the repository secret `KAGE_LIFE_KEYSTORE_BASE64`. The pipeline checks
its certificate against v35 before building. Debug alias and passwords retain the
Android defaults. It explicitly configures Gradle to use that key, checks the
finished APK against the previous artifact, and increases Android versionCode.

## If the original key is unavailable

A one-time save migration requires access to the user's device. The existing APK
is a debug build: authorised USB debugging can allow its WebView localStorage to
be exported without uninstalling it. Verify a backup of all occupied slots before
considering a new signing identity and reinstall. A future signing key must be
retained in a repository secret, not only a disposable build cache. This migration
has not been performed and requires coordination with the device owner.
