# Phone safe area v35

The status bar could cover close buttons in full-screen dialogs because the HTML viewport requested `cover`. The HUD's CSS padding did not protect those independent fixed overlays.

The viewport now requests `contain`. Capacitor 8.5 SystemBars therefore pads the native WebView parent by the actual system-bar and display-cutout insets, reducing the whole game viewport. Both the HUD and fixed dialogs stay inside that area, including after rotation and with gesture or button navigation. System bars stay visible with light icons against the dark game background. The offline shell cache is refreshed.

The final build applies `apply_phone_safe_area_v35.py` after the v34 gameplay patch. Mobile browser verification uses 360×740 and 412×855 content areas and checks the ninja close button is inside the viewport and clickable. These browser checks do not emulate Android's native system bars; native handling follows the installed Capacitor implementation in `plugin/SystemBars.java`.

Reference: https://capacitorjs.com/docs/apis/system-bars
