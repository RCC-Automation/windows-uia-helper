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
