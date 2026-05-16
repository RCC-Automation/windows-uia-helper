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

Start the helper service, then confirm it is healthy:

```powershell
cd "C:\Users\barru\Documents\New project\UI automation\windows-uia-helper"
.\.venv\Scripts\python -m uvicorn src.main:app --host 127.0.0.1 --port 8765
Invoke-RestMethod http://127.0.0.1:8765/health
```

The expected health result is:

```json
{"ok":true,"backend":"uia","screenshot_dependency":false}
```

If a background helper process will not stay alive from inside a sandboxed shell, start the same command as a persistent local process and re-check `/health` before continuing.

Open RobotStudio and load the virtual controller before AppStudio controller login. The validated route is:

1. Start `C:\Program Files (x86)\ABB\RobotStudio 2025\Bin\RobotStudio.exe`.
2. Click `Item_BackstageTabOpen`.
3. Select the recent project `Palletize Template_new`.
4. Click `Open`.
5. Wait for:

```text
Palletize Template_new - RobotStudio
Controller status: 1/1
GoFa10
```

Only after RobotStudio has this controller evidence, launch AppStudio through:

```powershell
.\.venv\Scripts\python examples\appstudio_devtools_probe.py
```

Confirm:

```powershell
Invoke-RestMethod "http://127.0.0.1:8765/chromium/status?port=9222"
```

The expected result is `ok=true`.

Validated 2026-05-16 evidence:

- RobotStudio title: `Palletize Template_new - RobotStudio`
- RobotStudio status: `Controller status: 1/1`
- AppStudio DevTools status: `ok=true` on port `9222`

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

In a 2026-05-16 run, clicking the visible `Palletizing` card label opened the designer and exposed the `Deploy` button through Chromium accessibility. Treat node ids from a specific run as temporary; find by accessible name/role each time.

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

Validated 2026-05-16 route:

1. UIA found AppStudio shell button `Connect to controller`.
2. The dialog exposed `Virtual controller` and `Log in as Default User`.
3. Selecting `Virtual controller` and clicking `Log in as Default User` closed the dialog.

If this dialog does not close, return to RobotStudio and verify `Palletize Template_new - RobotStudio`, `GoFa10`, and `Controller status: 1/1`.

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

Validated 2026-05-16 deploy evidence:

- Duplicate warning text: `The deployment path contains a duplicate file. Continuing will overwrite it.`
- After explicit operator approval, pressing `Continue` completed deployment.
- Success dialog text: `Palletizing is deployed!`
- Success dialog button: `Open in browser`

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

Use only the password explicitly provided by the operator in the current task/session. Do not hardcode controller passwords in committed scripts. If the operator wants a reusable local credential, use an ignored local secret such as `.env` or `.env.local`, for example:

```powershell
$env:APPSTUDIO_CONTROLLER_USER = "Default User"
$env:APPSTUDIO_CONTROLLER_PASSWORD = "robotics"
```

On this workstation, the operator may provide the local virtual-controller `Default User` password during the run. Ask for it when the Chrome login dialog appears instead of guessing.

Expected success: Chrome title changes to the deployed web app name, for example `Palletizing`.

Validated 2026-05-16 browser evidence after login:

- Chrome title: `Palletizing - Google Chrome`
- URL: `https://127.0.0.1:80/fileservice/$HOME/WebApps/Palletizing/index.html?nocache=<uuid>`
- Visible app text: `Palletizing`, `Production`, `Currently Palletizing`, `demo_pallet`, `Current layer 2/8`, `Total boxes placed 11/88`, `88 % Remaining`

If Chrome shows `Windows Hello` or a native `Anmelden` dialog after `Open in browser`, inspect the Chrome UIA tree for two `Edit` controls and the `Anmelden` button. Fill `Default User`, fill the operator-provided password, and press `Anmelden`.

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
- writing plaintext credentials into tracked repository files.

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

## Create A New Blank Project

Validated on 2026-05-14 by creating a short test project named:

```text
AITest01
```

Generated project folder:

```text
C:\Users\barru\Documents\AppStudio\Projects\AITest01
```

Generated files and folders included:

- `AITest01.aspproj`
- `WebAppData.json`
- `WebAppData_mini.json`
- `Assets/images/defaultIcon.png`
- `Assets/images/imageDefault.png`
- `Assets/images/tabDefault.png`
- `Languages/en.json`
- empty scaffold folders `CFG`, `MOD`, and `CustomFunctions`

### Leave An Open Project

When a project designer is open, use the breadcrumb in the upper-left AppStudio WebView:

```text
Projects > <project name> > <web app name>
```

To return to the front page/project list, click the middle breadcrumb project name. For the validated `Palletizing` run, clicking the first `Palletizing` breadcrumb link after `Projects` returned to the front page.

Do not click the final web app breadcrumb if the goal is to go back to the front page. The final entry represents the currently opened web app.

### Start New Project Dialog

From the front page:

1. Click `New project`.
2. The `Create a project` dialog opens.
3. Click `Project with a blank web app`.
4. The dialog switches to the `Property` tab.

Observed property fields:

- required `Location`, default:

```text
C:/Users/barru/Documents/AppStudio/Projects
```

- required `Web app name`, default observed:

```text
Webapp3
```

- `Width x Height (Wide)`, default:

```text
FlexPendant 1024 x 680 px
```

- checkbox:

```text
Enable compact screen
```

- group:

```text
Web app logo
```

- tabs:

```text
Property
Language
```

- footer buttons:

```text
Previous
Create
```

The dialog text says the web app name is also used as the project name and that a duplicate deployment name can replace the one with the duplicate name on the controller. Keep the name short; the operator expects names of about 20 characters or fewer.

### Fill And Create

For the validation, the name was changed through DOM/CDP from `Webapp3` to:

```text
AITest01
```

The textbox exposed through accessibility as:

```text
role: textbox
name: *Web app name
value: AITest01
```

Then click `Create`.

Expected result:

- the dialog closes;
- the project appears in the front-page project list/card list;
- the new card row includes `Project Icon`, project name, and creation date;
- clicking the card-row project name opens the new blank web app designer.

### Enter The New Blank Web App

After creation, AppStudio showed an `AITest01` project card row. Clicking the row label beside the icon/date opened the designer.

Verified designer state:

- breadcrumb:

```text
Projects > AITest01 > AITest01
```

- `Deploy` button is visible;
- `UI designer`, `Function`, and `Translation` tabs are visible;
- side panels include `Component`, `Structure`, `Appearance`, and `Behavior`;
- default blank-app starter content includes `This is a Text`, `Button`, and sample structure labels such as `text1`, `text2`, `text3`.

### Safety Notes For Future Agents

- Creating a new project writes to `C:\Users\barru\Documents\AppStudio\Projects`.
- Use a short, clearly disposable name unless the operator gives the real project name.
- Do not delete the generated project unless the operator explicitly asks.
- If the chosen name already exists, stop and ask before overwriting, replacing, or creating a duplicate variant.
- Do not add a custom logo or change advanced settings unless the operator asks; leave defaults during workflow discovery.

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

- Add reusable project-create logic:
  - click `New project`;
  - select `Project with a blank web app`;
  - fill `*Web app name`;
  - preserve or explicitly set `*Location`;
  - click `Create`;
  - verify generated files and open designer breadcrumb.

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
