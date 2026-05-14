# WebView / Chromium Accessibility Notes

## Purpose

The helper has two UI inspection backends:

- UI Automation for native Windows shell controls.
- Chromium DevTools Protocol accessibility for embedded WebView/browser content, when a local DevTools endpoint is exposed.

This split is intentional. AppStudio is an Avalonia desktop shell with an embedded Chromium/WebView content region. UI Automation can see the shell and some named Avalonia controls, but the rich project UI can collapse into generic Chromium host controls.

## AppStudio Probe Result

Observed AppStudio executable:

```text
C:\Program Files (x86)\ABB\AppStudio\AppStudio.Desktop.exe
```

Observed UIA shell controls:

- `Connect to controller`
- `ProjectButton`
- `ComponentButton`
- `CloudButton`
- `HelpButton`
- `SettingsButton`

Observed embedded content wrappers:

- `WebViewHandler`
- `webpackage`
- `BrowserRootView`
- `webpackage - Web content`

These wrappers confirm that AppStudio content is inside a Chromium/WebView layer. They do not guarantee that the inner DOM/accessibility tree is available through UIA.

## New Helper Endpoints

The Chromium endpoints assume a DevTools endpoint such as `127.0.0.1:9222`.

- `GET /chromium/status?host=127.0.0.1&port=9222`
- `GET /chromium/pages?host=127.0.0.1&port=9222`
- `POST /chromium/accessibility`
- `POST /chromium/find`

Request body for `/chromium/accessibility`:

```json
{
  "host": "127.0.0.1",
  "port": 9222,
  "page_id": null
}
```

Request body for `/chromium/find`:

```json
{
  "host": "127.0.0.1",
  "port": 9222,
  "page_id": null,
  "name": "Projects",
  "role": null,
  "contains": true
}
```

## How To Probe AppStudio

Start the helper:

```powershell
.\.venv\Scripts\python -m uvicorn src.main:app --host 127.0.0.1 --port 8765
```

Run the AppStudio probe:

```powershell
.\.venv\Scripts\python examples\appstudio_probe.py
```

The probe:

1. Starts AppStudio if no AppStudio window is visible.
2. Confirms UIA can see known shell controls.
3. Checks common Chromium DevTools ports.
4. If a port is reachable, lists pages and searches the Chromium accessibility tree for `Projects`.

## Important Limitation

The helper cannot force an arbitrary embedded WebView to expose DevTools. If `/chromium/status` returns `DEVTOOLS_NOT_REACHABLE`, future work should investigate AppStudio/WebView2 launch options or environment variables for remote debugging.

Possible areas to investigate:

- Whether AppStudio accepts Chromium/WebView2 command-line flags.
- Whether AppStudio honors WebView2 environment configuration.
- Whether AppStudio writes WebView2 user data folders that reveal runtime arguments.
- Whether ABB documents a developer/debug mode for AppStudio.

Until such a port is available, the helper can still operate native AppStudio shell controls through UIA, but cannot reliably inspect the inner project UI as structured Chromium accessibility nodes.

## WebView2 Remote Debugging Path

Microsoft documents `WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS` as a way to pass extra browser arguments to WebView2, including:

```text
--remote-debugging-port=9222
```

The same Microsoft guidance also describes a policy registry route under:

```text
HKEY_CURRENT_USER\Software\Policies\Microsoft\Edge\WebView2\AdditionalBrowserArguments
```

with an app-specific value such as:

```text
AppStudio.Desktop.exe = --remote-debugging-port=9222
```

Use the environment-variable route first because it is reversible and does not modify machine policy:

```powershell
.\.venv\Scripts\python examples\appstudio_devtools_probe.py
```

If AppStudio is already running, close it fully before using this probe. Many WebView2 apps are single-instance applications; launching a second copy may simply activate the existing process, which means the new environment variable will not be applied.

Reference:

- Microsoft Learn, Debug WebView2 apps with Visual Studio Code: https://learn.microsoft.com/microsoft-edge/webview2/how-to/debug-visual-studio-code
