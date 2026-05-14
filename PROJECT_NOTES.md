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
