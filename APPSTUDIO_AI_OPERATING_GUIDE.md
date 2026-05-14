# AppStudio AI Operating Guide

This guide is for a future Codex/AppStudio AI thread that needs to develop AppStudio projects, connect to a RobotStudio virtual controller, deploy, test the deployed web app, and feed findings back into the next implementation iteration.

## Current Assessment

The project is sufficient for a supervised proof-of-work loop:

1. Open AppStudio with WebView2 DevTools enabled.
2. Inspect AppStudio's start page and project designer through structured Chromium accessibility.
3. Open an existing project from the project-card row.
4. Use native UI Automation for AppStudio shell controls such as `Connect to controller`.
5. Connect to a RobotStudio virtual controller through the default-user login route.
6. Deploy an opened project to the controller.
7. Open the deployed web app in Chrome.
8. Log in to the deployed web app.
9. Inspect and navigate the deployed app through DOM/CDP.

The project is not yet sufficient for a fully autonomous AppStudio development loop. The main gaps are:

- no single high-level scenario runner that performs the whole AppStudio journey end to end;
- no durable project-selection abstraction beyond the observed `Palletizing` project row;
- no implemented "create new AppStudio project" workflow;
- no automated local-folder deployment workflow;
- no controller-state validation beyond deployed web app DOM inspection;
- no AppStudio designer editing actions beyond navigation and deployment;
- no robust recovery logic when AppStudio, Chrome, RobotStudio, or the controller is already in an unexpected state.

Use the helper as a supervised automation foundation, not as a complete AppStudio agent yet.

## Required Runtime Pieces

- AppStudio executable:

```text
C:\Program Files (x86)\ABB\AppStudio\AppStudio.Desktop.exe
```

- Helper service:

```powershell
.\.venv\Scripts\python -m uvicorn src.main:app --host 127.0.0.1 --port 8765
```

- AppStudio WebView2 DevTools launch:

```powershell
.\.venv\Scripts\python examples\appstudio_devtools_probe.py
```

- AppStudio WebView DevTools endpoint:

```text
http://127.0.0.1:9222
```

- Optional deployed-app Chrome/CDP endpoint:

```text
http://127.0.0.1:9333
```

- RobotStudio must have a virtual controller running before AppStudio controller login is expected to succeed.

## Known Working Journey

### 1. Start Cleanly

Close AppStudio before launching it with WebView2 debugging. AppStudio may behave like a single-instance app, so starting a second process can reuse the old process and ignore the new `WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS` environment variable.

Start the helper service, then launch AppStudio through:

```powershell
.\.venv\Scripts\python examples\appstudio_devtools_probe.py
```

Confirm:

```powershell
Invoke-RestMethod "http://127.0.0.1:8765/chromium/status?port=9222"
```

The expected result is `ok=true`.

### 2. Open An Existing Project

Use Chromium accessibility on port `9222`.

The start page exposes project content such as:

- `Projects`
- `Search`
- `Palletizing`
- `Web app`
- date/time labels

To open `Palletizing`, click the project card row label beside the project icon/date. Do not click the left-side list label if the card row is available. In the validated run, this row exposed:

- `Project Icon`
- `Palletizing`
- `Web app`
- `5/11/2026, 7:25:55 AM`

Once opened, the designer exposes:

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

### 3. Connect To Controller

Use UI Automation, not Chromium, for the shell button:

```text
Connect to controller
```

The login dialog is an AppStudio child window with:

- title: `Log in to controller`
- class: `RobotLogin`
- option: `Virtual controller`
- action: `Log in as Default User`

Select `Virtual controller`, then click `Log in as Default User`.

If no virtual controller is running in RobotStudio, this will not complete. The expected success condition is that the login dialog closes.

### 4. Deploy To Controller

After controller login succeeds, click the Chromium `Deploy` button in the AppStudio designer.

The deploy modal exposes:

- `Controller` radio, selected by default;
- `Local file path` radio;
- final `Deploy` button.

Click final `Deploy`.

If `Duplicate file found` appears, the `Continue` button overwrites the existing controller deployment. This is acceptable only when the operator has approved an intentional redeploy. Otherwise stop and ask.

Expected success:

- `Palletizing is deployed!`
- `You can open your web app in teach pendant now.`
- buttons `Open in browser` and `OK`

### 5. Open And Log In To The Deployed App

Click `Open in browser`.

Chrome opens a URL like:

```text
http://127.0.0.1:80/fileservice/$HOME/WebApps/Palletizing/index.html?nocache=<uuid>
```

Chrome shows a native login prompt for:

```text
https://127.0.0.1:80
```

UIA sees:

- username edit: `Nutzername`
- password edit: `Passwort`
- submit button: `Anmelden`

Use username:

```text
Default User
```

Use only the password explicitly provided by the operator in the current task/session. Do not store it in documentation or logs.

Expected success: Chrome title changes to the deployed web app name, for example `Palletizing`.

### 6. Inspect The Deployed App Programmatically

For DOM inspection, use a separate debug-enabled Chrome instance because the AppStudio-opened Chrome may not expose DevTools.

Validated command:

```powershell
.\.venv\Scripts\python examples\deployed_webapp_probe.py --password <password>
```

Important:

- Use HTTPS, not plain HTTP, for the debug-controlled browser:

```text
https://127.0.0.1:80/fileservice/$HOME/WebApps/Palletizing/index.html
```

- Ignore certificate errors through CDP with `Security.setIgnoreCertificateErrors`.
- Avoid printing or committing passwords.

Validated deployed-app navigation by DOM click:

- `Production`
- `Tuning`
- `Recipe configuration`
- `Pattern builder`

These menu entries are custom HTML elements:

```text
.fp-components-hamburgermenu-a-menu__button
```

## Safety Rules

Stop and ask before:

- overwriting a deployment unless the operator has already approved redeploy overwrite for the task;
- clicking production runtime controls such as `Abort pallet`, `Start new pallet`, `Stop immediately`, `Resume`, or pallet-state changes;
- deleting or replacing AppStudio projects;
- changing controller state outside the explicitly requested test;
- using credentials that were not provided in the active task/session.

Safe by default:

- opening AppStudio;
- observing UIA trees;
- observing Chromium accessibility trees;
- opening an existing project;
- navigating AppStudio designer tabs;
- navigating deployed app read-only views;
- deploying only after the operator has agreed to the target and overwrite behavior.

## Development Loop Target

The intended future AI loop should be:

1. Modify AppStudio project source/generator files in the workspace.
2. Open or reload the project in AppStudio.
3. Connect to the virtual controller.
4. Deploy to the controller or a local output folder.
5. Open the deployed app.
6. Programmatically inspect DOM/state.
7. Run targeted user-journey tests.
8. Record findings.
9. Feed findings into the next implementation iteration.
10. Commit the verified code and documentation.

The current repo supports steps 2 through 6 for an existing project, with supervision. Steps 1, 7, 8, 9, and 10 still depend on the surrounding AppStudio project repository and the future scenario runner.

## Missing Capabilities To Implement Next

### High Priority

- Create an `examples/appstudio_full_journey.py` scenario runner:
  - start helper or verify it is running;
  - launch AppStudio with WebView2 DevTools;
  - open a named project;
  - connect to virtual controller;
  - deploy to controller;
  - optionally open deployed app;
  - return a structured JSON report.

- Add reusable project-open logic:
  - find project cards by name and type;
  - prefer card-row labels beside project icon/date;
  - verify designer breadcrumb after opening.

- Add reusable controller-login logic:
  - find `Connect to controller`;
  - select virtual controller;
  - click default-user login;
  - detect success/failure from dialog state.

- Add reusable deploy logic:
  - select controller or local folder target;
  - handle duplicate-file warning with an explicit `allow_overwrite` flag;
  - detect success dialog and optionally open browser.

- Add deployed-app DOM test helpers:
  - navigate menu by visible label;
  - collect visible text;
  - find custom AppStudio component elements by text and component id;
  - support read-only assertions first.

### Medium Priority

- Implement local-folder deployment exploration:
  - select `Local file path`;
  - choose a workspace output folder;
  - document generated files;
  - compare local output with controller output.

- Implement new-project creation exploration:
  - click `New project`;
  - capture required fields and templates;
  - create a disposable test project only after operator approval;
  - document project file locations and cleanup rules.

- Add recovery checks:
  - detect stale AppStudio process without DevTools;
  - detect missing RobotStudio virtual controller;
  - detect Chrome profile/login prompt issues;
  - detect certificate/auth failures on deployed app.

- Add run artifacts:
  - save JSON reports under an ignored `runs/` folder;
  - include timestamps, AppStudio project name, deploy target, browser URL, visible deployed-app state, and safety decisions.

### Lower Priority

- Add direct CDP DOM query endpoints to the FastAPI helper, not only accessibility-tree endpoints.
- Add semantic wrappers for AppStudio designer tabs and GraphView nodes.
- Investigate whether AppStudio internal routes can open projects more directly than clicking project cards.
- Investigate controller APIs for deeper validation beyond the deployed app DOM.

## Conclusion

The current project proves that an AI thread can work with AppStudio and the deployed controller web app through structured automation, without screenshots. It is not yet a complete development agent. The next engineering step is to turn the proven manual sequence into reusable scenario runners with explicit safety flags and structured reports.
