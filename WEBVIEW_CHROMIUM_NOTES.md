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
- `POST /chromium/click`

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

Request body for `/chromium/click`:

```json
{
  "host": "127.0.0.1",
  "port": 9222,
  "page_id": null,
  "node_id": "219",
  "name": null,
  "role": null,
  "contains": true,
  "click_count": 2
}
```

`/chromium/click` resolves an accessibility node to its `backendDOMNodeId`, reads the DOM box through CDP, and dispatches mouse events at the element center. This is still structured WebView automation; it is not screenshot recognition.

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
--remote-debugging-port=9222 --remote-allow-origins=http://127.0.0.1:9222
```

The same Microsoft guidance also describes a policy registry route under:

```text
HKEY_CURRENT_USER\Software\Policies\Microsoft\Edge\WebView2\AdditionalBrowserArguments
```

with an app-specific value such as:

```text
AppStudio.Desktop.exe = --remote-debugging-port=9222 --remote-allow-origins=http://127.0.0.1:9222
```

Use the environment-variable route first because it is reversible and does not modify machine policy:

```powershell
.\.venv\Scripts\python examples\appstudio_devtools_probe.py
```

If AppStudio is already running, close it fully before using this probe. Many WebView2 apps are single-instance applications; launching a second copy may simply activate the existing process, which means the new environment variable will not be applied.

## 2026-05-14 Breakthrough Result

After fully closing AppStudio and launching it with:

```text
WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS=--remote-debugging-port=9222
```

the helper reached the WebView2 DevTools endpoint:

- Browser: `Edg/148.0.3967.54`
- Page title: `webpackage`
- Page URL: `file:///C:/Program Files (x86)/ABB/AppStudio/Assets/webpackage/index.html`

The Chromium accessibility tree exposed semantic AppStudio project-page content, including:

- `New project`
- `Open project`
- `Projects`
- `Search`
- `Palletizing`
- `Web app`
- `WebAppSignalSetupDem`
- `WebAppScrewdriverQC2`
- `QuickConfigUsage`
- `WebAppScrewdriver`
- `Webapp1`
- `Webapp2`
- `Import`
- `Export`

Verified WebView control:

- `/chromium/find` finds nodes such as `Projects` and `Palletizing`.
- `/chromium/click` can dispatch clicks against WebView accessibility nodes.
- Clicking and double-clicking the visible `Palletizing` text node selected/hovered the project and revealed the `.aspproj` tooltip, but did not open the project. Future work should find the parent card/open affordance or invoke the internal route/action directly through CDP.

Current conclusion:

- We can now inspect AppStudio WebView content semantically.
- We can dispatch WebView clicks through CDP.
- We cannot yet claim full GraphView control, because the project/GraphView was not opened in this validation pass.

## 2026-05-14 Project Open And Controller Deploy Journey

Verified route from AppStudio start page into the project designer:

1. Fully close AppStudio.
2. Start the helper server.
3. Launch AppStudio with WebView2 DevTools enabled:

```powershell
.\.venv\Scripts\python examples\appstudio_devtools_probe.py
```

4. Confirm `/chromium/status?port=9222` returns `ok=true`.
5. On the project page, identify the project card row. For `Palletizing`, the row exposes:
   - `Project Icon`
   - `Palletizing`
   - `Web app`
   - `5/11/2026, 7:25:55 AM`
6. Click the lower card-row `Palletizing` label beside the icon/date. This is not the left-list `Palletizing` text. In the validation run, the opening click targeted node `243`.
7. The project designer opens and exposes:
   - `Breadcrumb`
   - `Projects > Palletizing`
   - `Deploy`
   - `UI designer`
   - `Function`
   - `Translation`
   - `Component`
   - `Structure`
   - `Appearance`
   - `Behavior`
   - project/canvas text such as `Pattern builder`, `Palletizing | Production`, `Currently Palletizing`, and `Pattern name:`

Verified controller connection route:

1. Use UI Automation, not Chromium, for the native shell button `Connect to controller`.
2. Invoke/click `Connect to controller`.
3. A child window inside AppStudio appears with class `RobotLogin` and title `Log in to controller`.
4. Select `Virtual controller`.
5. Click `Log in as Default User`.
6. If a virtual controller is running in RobotStudio, the login dialog closes. If no virtual controller is running, the dialog remains open. The dialog includes a required `Controller IP` field and warning text: `If multiple controllers are started in RobotStudio, please shut down those that are not needed.`

Verified controller deployment route:

1. After controller login succeeds, click Chromium node `Deploy` in the project designer.
2. The modal `Deploy web app` opens.
3. It exposes:
   - `Controller` radio, selected by default.
   - `Local file path` radio, alternate target.
   - settings text for responsive layout, sequential deployment, and JavaScript compression.
   - final `Cancel` and `Deploy` buttons.
4. Click final `Deploy`.
5. If an older deployment exists, AppStudio opens `Duplicate file found`:
   - Message: `The deployment path contains a duplicate file. Continuing will overwrite it.`
   - Buttons: `Cancel`, `Continue`
6. Treat `Continue` as an overwrite confirmation. It is appropriate for an intentional redeploy, but future agents should stop and ask if overwrite has not been approved.
7. After pressing `Continue`, deployment completed successfully in this run.
8. Success dialog:
   - `Palletizing is deployed!`
   - `You can open your web app in teach pendant now.`
   - Buttons: `Open in browser`, `OK`
9. Pressing `Open in browser` opened Chrome at:

```text
http://127.0.0.1:80/fileservice/$HOME/WebApps/Palletizing/index.html?nocache=<uuid>
```

Notes:

- The Chrome instance opened by AppStudio did not expose an obvious remote-debugging port in this validation.
- AppStudio WebView DevTools on `9222` remains for AppStudio itself, not necessarily for the deployed app browser.
- Raw `Invoke-WebRequest` to the controller fileservice URL failed with `The underlying connection was closed`, even though Chrome opened the page. Browser-side inspection needs a separate Chrome-debugging strategy or another controller-compatible HTTP client path.
- Do not press overwrite/continue automatically unless the user has approved redeployment overwrite behavior.

Reference:

- Microsoft Learn, Debug WebView2 apps with Visual Studio Code: https://learn.microsoft.com/microsoft-edge/webview2/how-to/debug-visual-studio-code

## 2026-05-14 Deployed Web App Browser Journey

After pressing `Open in browser`, Chrome opens the deployed web app at a controller file-service URL similar to:

```text
http://127.0.0.1:80/fileservice/$HOME/WebApps/Palletizing/index.html?nocache=<uuid>
```

Chrome immediately shows a native login prompt. The prompt is not part of the app DOM; UI Automation sees it as a Chrome dialog:

- title: `Anmelden`
- origin label: `https://127.0.0.1:80`
- username edit: `Nutzername`
- password edit: `Passwort`
- submit button: `Anmelden`

Verified credentials for the local RobotStudio virtual controller web app:

- username: `Default User`
- password: provided by the operator for the session

After submitting those credentials, the browser title changed to `Palletizing`, confirming that the deployed app opened.

### Programmatic Browser Access

The AppStudio-opened Chrome instance is useful for the human journey, but it does not necessarily expose a DevTools port. For DOM-level automation, launch a separate Chrome instance with DevTools and navigate to the HTTPS controller endpoint:

```powershell
.\.venv\Scripts\python examples\deployed_webapp_probe.py --password <password>
```

Important details:

- Use `https://127.0.0.1:80/fileservice/$HOME/WebApps/Palletizing/index.html`, not the plain HTTP URL, for the debug-controlled browser.
- The controller presents a self-signed or untrusted certificate. CDP must call `Security.setIgnoreCertificateErrors` before navigation.
- Supplying credentials in the URL works for the local validation path:

```text
https://Default%20User:<password>@127.0.0.1:80/fileservice/$HOME/WebApps/Palletizing/index.html
```

Avoid printing the password in logs. Prefer passing it as an argument or secret when this becomes a durable automation flow.

### Verified Deployed App State

The deployed app DOM was readable through CDP. Initial Production view text included:

- `Palletizing | Production`
- `Currently Palletizing`
- `demo_pallet`
- `Abort pallet`
- `Actions`
- `Start new pallet`
- `Stop immediately`
- `Resume`
- `Pallet status`
- `Pallet 1 Active`
- `Pallet 2 Full`
- `Pattern name: demo_pattern_2`
- `Current layer 2/8`
- `Total boxes placed 11/88`
- `88 % Remaining`

The app shell uses custom HTML components rather than semantic native buttons in many places. Querying `button,input,select,textarea,[role=button]` returned no controls on the Production page, but direct DOM inspection found clickable custom menu entries:

```text
.fp-components-hamburgermenu-a-menu__button
```

Verified safe navigation by DOM click:

- `Production`
- `Tuning`
- `Recipe configuration`
- `Pattern builder`

Observed page texts:

- `Palletizing | Tuning`, with box and motion tuning sections.
- `Palletizing | Recipe configuration | demo_pallet`, with recipes `demo_pallet-2`, `demo_pallet`, and `demo_pallet_Copy`.
- `Palletizing | Pattern design`, with patterns `aaa`, `demo_pattern_1`, and `demo_pattern_2`.

### Safety Boundary

Navigation between app views is safe. Production actions such as `Abort pallet`, `Start new pallet`, `Stop immediately`, `Resume`, and pallet-state changes may affect the controller state. Future agents should not click those controls unless the operator explicitly asks for that runtime action.
