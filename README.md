# Windows UI Automation Helper

Local Windows UI Automation helper for AI agents. It exposes the active Windows UI as structured JSON and can execute constrained UI actions without screenshot analysis.

## Status

Initial implementation for the first priority slice:

- `GET /health`
- `GET /windows`
- `GET /active-window`
- `GET /tree`
- `GET /observe`
- `POST /find`
- `POST /action` with `focus`, `invoke`, and click actions
- `POST /type`
- `POST /hotkey`
- Optional Chromium DevTools accessibility endpoints for embedded WebView/browser content
- Notepad demo
- AppStudio/WebView probe

## Install

Python 3.11+ is the target runtime.

```powershell
cd "C:\Users\barru\Documents\New project\UI automation\windows-uia-helper"
py -m venv .venv
.\.venv\Scripts\python -m pip install --upgrade pip
.\.venv\Scripts\python -m pip install -r requirements.txt
```

## Run

The service must bind to localhost only.

```powershell
.\.venv\Scripts\python -m uvicorn src.main:app --host 127.0.0.1 --port 8765
```

Health check:

```powershell
Invoke-RestMethod http://127.0.0.1:8765/health
```

## Example API Calls

List visible top-level windows:

```powershell
Invoke-RestMethod http://127.0.0.1:8765/windows
```

Observe the active window:

```powershell
Invoke-RestMethod http://127.0.0.1:8765/observe
```

Find an edit control:

```powershell
$body = @{ control_type = "Edit"; contains = $true } | ConvertTo-Json
Invoke-RestMethod http://127.0.0.1:8765/find -Method Post -Body $body -ContentType "application/json"
```

Type into a found element:

```powershell
$body = @{ element_id = "<id>"; text = "Hello from UI Automation"; clear_first = $true } | ConvertTo-Json
Invoke-RestMethod http://127.0.0.1:8765/type -Method Post -Body $body -ContentType "application/json"
```

Invoke an element:

```powershell
$body = @{ element_id = "<id>"; action = "invoke" } | ConvertTo-Json
Invoke-RestMethod http://127.0.0.1:8765/action -Method Post -Body $body -ContentType "application/json"
```

Send an allowed hotkey:

```powershell
$body = @{ keys = @("ctrl", "s") } | ConvertTo-Json
Invoke-RestMethod http://127.0.0.1:8765/hotkey -Method Post -Body $body -ContentType "application/json"
```

## Notepad Demo

Start the server, then run:

```powershell
.\.venv\Scripts\python examples\notepad_demo.py
```

The demo opens Notepad, observes the active window, finds an edit/document element, types `Hello from UI Automation`, sends `ctrl+s`, and observes the Save dialog.

## AppStudio Probe

Start the server, then run:

```powershell
.\.venv\Scripts\python examples\appstudio_probe.py
```

The probe starts AppStudio if needed, confirms the native UIA shell controls, checks common Chromium DevTools ports, and searches Chromium accessibility if a port is reachable.

See [WEBVIEW_CHROMIUM_NOTES.md](WEBVIEW_CHROMIUM_NOTES.md) for the current AppStudio-specific findings and next investigation points.

For future Codex/AppStudio AI threads, start with [APPSTUDIO_AI_OPERATING_GUIDE.md](APPSTUDIO_AI_OPERATING_GUIDE.md). It summarizes the validated AppStudio/controller/deployed-browser journey, the safety boundaries, and the missing capabilities needed for a full iterative development loop.

To launch AppStudio with a temporary WebView2 remote-debugging environment variable and wait for the DevTools endpoint:

```powershell
.\.venv\Scripts\python examples\appstudio_devtools_probe.py
```

If AppStudio is already running, close it fully before using this probe so the environment variable applies to the first AppStudio process.

## Chromium / WebView Accessibility

AppStudio exposes its native shell through UI Automation, but its central content area is an embedded Chromium/WebView surface. UIA currently reports that area as objects such as `WebViewHandler`, `webpackage`, `BrowserRootView`, and `webpackage - Web content`, rather than exposing every project card or web label as first-class UIA controls.

The helper therefore includes an optional Chromium DevTools Protocol layer. It works only when the embedded WebView or browser process exposes a local DevTools endpoint, usually on `127.0.0.1:9222` or another explicitly configured debugging port.

Chromium endpoints:

- `GET /chromium/status`
- `GET /chromium/pages`
- `POST /chromium/accessibility`
- `POST /chromium/find`

Check for a DevTools endpoint:

```powershell
Invoke-RestMethod "http://127.0.0.1:8765/chromium/status?port=9222"
```

List debuggable Chromium pages:

```powershell
Invoke-RestMethod "http://127.0.0.1:8765/chromium/pages?port=9222"
```

Fetch the full compact accessibility tree for the first debuggable page:

```powershell
$body = @{ host = "127.0.0.1"; port = 9222 } | ConvertTo-Json
Invoke-RestMethod http://127.0.0.1:8765/chromium/accessibility -Method Post -Body $body -ContentType "application/json"
```

Search Chromium accessibility nodes:

```powershell
$body = @{ host = "127.0.0.1"; port = 9222; name = "Projects"; contains = $true } | ConvertTo-Json
Invoke-RestMethod http://127.0.0.1:8765/chromium/find -Method Post -Body $body -ContentType "application/json"
```

Click a Chromium accessibility node by text or node id:

```powershell
$body = @{ host = "127.0.0.1"; port = 9222; name = "Palletizing"; contains = $true; click_count = 2 } | ConvertTo-Json
Invoke-RestMethod http://127.0.0.1:8765/chromium/click -Method Post -Body $body -ContentType "application/json"
```

If `/chromium/status` returns `DEVTOOLS_NOT_REACHABLE`, the WebView is not currently exposing a DevTools endpoint. In that case, future work should investigate whether AppStudio can be launched with a WebView2/Chromium remote-debugging flag or environment option. Do not fall back to screenshots for v1 unless the project explicitly changes direction.

## Security Model

- The server is intended for `127.0.0.1` only.
- The helper never executes arbitrary shell commands through the API.
- Actions are constrained by an allowlist.
- Risky labels such as Delete, Remove, Send, Pay, Submit, Install, Uninstall, Overwrite, Password, Credential, or Close require `confirm=true`.
- `alt+f4` is intentionally not allowed.
- Prefer UI Automation control patterns before mouse-input fallback.

The initial process allowlist is:

- `notepad.exe`
- `calc.exe`
- `CalculatorApp.exe`
- `RobotStudio.exe`
- `AppStudio.Desktop.exe`

If the active window process cannot be resolved, the service does not block it yet. Tightening this requires reliable process-name detection in the local environment.

## Limitations

- Some applications expose poor UI Automation metadata.
- Canvas-based or custom-rendered applications may not expose meaningful controls.
- Applications running as administrator may require this helper to also run elevated.
- Element IDs are temporary and only intended to remain valid between one observe/find and action cycle.
- Screenshots are intentionally not used in v1.
