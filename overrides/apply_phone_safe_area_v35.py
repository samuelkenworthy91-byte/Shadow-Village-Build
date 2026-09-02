"""Fit the complete game WebView inside the phone's system bars and cutouts.

Run after v34. Capacitor 8 SystemBars applies native parent-view insets when
the viewport does not request `cover`; this protects fixed dialogs as well as
the HUD. No fixed pixel offset or scaling is needed when the phone rotates.
"""
from pathlib import Path

APP = Path(__file__).resolve().parents[1] / 'app'


def replace_once(relative, before, after):
    path = APP / relative
    source = path.read_text()
    if after in source and before not in source:
        return
    if source.count(before) != 1:
        raise SystemExit(f'v35: unexpected source in {relative}; reconcile before applying')
    path.write_text(source.replace(before, after, 1))


replace_once('index.html', 'viewport-fit=cover', 'viewport-fit=contain')
replace_once(
    'capacitor.config.ts',
    '  plugins: {\n    SplashScreen:',
    '  plugins: {\n'
    '    // Keep the whole WebView inside system bars, including fixed pop-ups.\n'
    '    // viewport-fit=contain selects native inset handling in Capacitor 8.\n'
    '    SystemBars: {\n'
    '      insetsHandling: "css",\n'
    '      style: "DARK",\n'
    '      hidden: false,\n'
    '    },\n'
    '    SplashScreen:',
)
replace_once('public/sw.js', 'kage-life-v6-clans-summons', 'kage-life-v7-phone-safe-area')
print('v35: game viewport fits inside phone status/navigation bars and display cutouts')
