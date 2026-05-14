# Project Notes

## 2026-05-14 Initial Validation

The first live validation used Notepad.

Result:

- The helper opened Notepad.
- `/health` returned successfully.
- `/observe` read the active Notepad window through UI Automation.
- `/find` located the `Text Editor` element.
- `/type` inserted `Hello from UI Automation`.
- `/hotkey` sent `ctrl+s`.
- `/observe` then read the native `Save As` dialog as structured UIA controls.

Important implementation correction:

- `pywinauto.Desktop(backend="uia").active()` was not available in the installed pywinauto version.
- Active-window lookup now uses `win32gui.GetForegroundWindow()` and reconnects that handle through UIA.

## AppStudio Validation

AppStudio executable:

```text
C:\Program Files (x86)\ABB\AppStudio\AppStudio.Desktop.exe
```

Observed process/window:

- Process: `AppStudio.Desktop`
- Window title: `AppStudio`
- Class name: `MainWindow`

UIA exposed useful shell controls:

- `Connect to controller`
- `ProjectButton`
- `ComponentButton`
- `CloudButton`
- `HelpButton`
- `SettingsButton`
- window controls

UIA limitation:

- The main content region is embedded Chromium/WebView content.
- UIA reports it mostly as `WebViewHandler`, `webpackage`, `BrowserRootView`, and `webpackage - Web content`.
- Project cards and richer web UI labels were not exposed as normal UIA controls in the initial probe.

Follow-up direction:

- Keep UIA as the base desktop-shell backend.
- Use Chromium DevTools Protocol accessibility when AppStudio/WebView exposes a local debugging endpoint.
- Do not use screenshots as the primary v1 path.

## 2026-05-14 AppStudio Project Deploy Validation

Breakthrough:

- AppStudio opened with WebView2 DevTools on `127.0.0.1:9222`.
- The helper opened the `Palletizing` project by clicking the project-card row label beside the project icon/date.
- The project designer became visible through Chromium accessibility.
- The helper connected to a RobotStudio virtual controller:
  - UIA button: `Connect to controller`
  - Dialog: `Log in to controller`
  - Option: `Virtual controller`
  - Action: `Log in as Default User`
- The helper deployed to controller:
  - Chromium button: `Deploy`
  - Dialog: `Deploy web app`
  - Target: `Controller` selected by default
  - Confirmation: `Duplicate file found`
  - Approved action: `Continue`
  - Result: `Palletizing is deployed!`
- `Open in browser` opened Chrome to the controller fileservice URL for the deployed web app.

Safety note:

- `Continue` in the duplicate-file dialog overwrites an existing deployment. It is acceptable for intentional redeploys, but future agents should ask before pressing it unless overwrite has already been approved for the task.

## 2026-05-14 Deployed Web App Login And DOM Validation

The deployed browser journey is now validated end to end:

- `Open in browser` launches Chrome to the controller file-service URL.
- Chrome shows a native login prompt for `https://127.0.0.1:80`.
- UIA can fill the prompt fields `Nutzername` and `Passwort` and press `Anmelden`.
- Login as `Default User` with the operator-provided password opened the deployed `Palletizing` web app.

For programmatic DOM access, a separate debug-enabled Chrome instance worked when using:

- endpoint: `https://127.0.0.1:80/fileservice/$HOME/WebApps/Palletizing/index.html`
- CDP port: `9333`
- CDP setting: `Security.setIgnoreCertificateErrors`
- credentials embedded only for local validation

`examples/deployed_webapp_probe.py` captures this route and prints the deployed app title, URL, visible text, and hamburger-menu entries.

Confirmed DOM-level navigation:

- Production
- Tuning
- Recipe configuration
- Pattern builder

Do not automate runtime-affecting production actions without explicit operator approval.
