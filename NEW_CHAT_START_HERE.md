# New Chat Start Here

Read this first when a new Codex chat is asked to work with AppStudio, RobotStudio, FlexPendant, or this Windows UI automation helper.

## What This Repository Is For

This repository gives AI agents a structured way to operate ABB desktop workflows without relying on screenshots.

The target workflow is:

1. Develop or modify an AppStudio project.
2. Open AppStudio and load/create the project.
3. Connect AppStudio to a RobotStudio virtual controller.
4. Deploy the AppStudio web app to the controller.
5. Validate the deployment in a browser and in FlexPendant.
6. Use observations from the deployed runtime to guide the next implementation iteration.

The helper exposes Windows UI Automation and Chromium/WebView accessibility through local APIs and scripts. It is not a full autonomous agent yet; it is a supervised automation foundation.

## Read These Guides In Order

1. [APPSTUDIO_AI_OPERATING_GUIDE.md](APPSTUDIO_AI_OPERATING_GUIDE.md)
   - How to launch AppStudio with WebView2 DevTools.
   - How to leave an open project.
   - How to open an existing project.
   - How to create a new blank project.
   - How to connect to a virtual controller.
   - How to deploy to the controller.
   - How to open and inspect the deployed browser app.

2. [ROBOTSTUDIO_AI_OPERATING_GUIDE.md](ROBOTSTUDIO_AI_OPERATING_GUIDE.md)
   - How to start RobotStudio.
   - How to open a recent project.
   - How to confirm the virtual controller is loaded.
   - How to warm-restart the controller when explicitly requested.
   - How to launch FlexPendant from RobotStudio.

3. [FLEXPENDANT_AI_OPERATING_GUIDE.md](FLEXPENDANT_AI_OPERATING_GUIDE.md)
   - Why FlexPendant is important.
   - How to open it.
   - How to find and open a deployed app such as `Palletizing`.
   - What the helper can see inside the real pendant-hosted app.
   - Which runtime actions are dangerous and require explicit approval.

4. [WEBVIEW_CHROMIUM_NOTES.md](WEBVIEW_CHROMIUM_NOTES.md)
   - Lower-level WebView2 and Chromium DevTools details.
   - AppStudio WebView debugging setup.
   - Browser/CDP details for deployed app inspection.

5. [PROJECT_NOTES.md](PROJECT_NOTES.md)
   - Chronological validation evidence.
   - What was actually tried and verified.

## Core Mental Model

There are three main surfaces:

- **AppStudio**: authoring and deployment tool. Use it to open/create projects, connect to controller, and deploy.
- **RobotStudio**: virtual-controller host. Use it to load the station/project and keep the virtual controller available.
- **FlexPendant**: realistic operator/runtime validation surface. Use it to verify the deployed app as it appears on the controller/pendant side.

Use the right automation backend for each surface:

- Native Windows UIA for RobotStudio ribbon, dialogs, status bars, and FlexPendant shell.
- Chromium DevTools accessibility for AppStudio WebView content when AppStudio is launched with WebView2 debugging.
- UIA or CDP for deployed web apps depending on where they are opened.
- FlexPendant UIA for final deployed-app validation in the pendant host.

Do not use screenshots as the primary strategy.

## Start The Helper

From this repository:

```powershell
cd "C:\Users\barru\Documents\New project\UI automation\windows-uia-helper"
.\.venv\Scripts\python -m uvicorn src.main:app --host 127.0.0.1 --port 8765
```

Health check:

```powershell
Invoke-RestMethod http://127.0.0.1:8765/health
```

Expected healthy response:

```json
{"ok":true,"backend":"uia","screenshot_dependency":false}
```

If a background helper launched from Codex does not remain reachable, start the same uvicorn command as a persistent local process and re-check `/health`.

## AppStudio Quick Route

AppStudio executable:

```text
C:\Program Files (x86)\ABB\AppStudio\AppStudio.Desktop.exe
```

Launch with WebView2 DevTools:

```powershell
.\.venv\Scripts\python examples\appstudio_devtools_probe.py
```

Important: close AppStudio fully before launching through this probe, otherwise the WebView2 debug environment variable may not apply.

Expected DevTools endpoint:

```text
127.0.0.1:9222
```

Validated existing-project route:

- From the front page, click the project card row label beside icon/date, not only the left-list label.
- For `Palletizing`, this opened the designer.

Validated leave-project route:

- Click the middle breadcrumb project name in `Projects > <project name> > <web app name>`.

Validated new-project route:

- `New project`
- `Create a project`
- `Project with a blank web app`
- set short `*Web app name`
- keep default location unless the operator says otherwise
- `Create`
- click the new project card row to enter the blank designer

Validated controller connection route:

- Use UIA for native AppStudio shell button `Connect to controller`.
- RobotStudio should already show `Palletize Template_new - RobotStudio`, `GoFa10`, and `Controller status: 1/1`.
- Select `Virtual controller`.
- Click `Log in as Default User`.

Validated deploy route:

- Click `Deploy`.
- Use `Controller` target unless another target is requested.
- If duplicate-file warning appears, `Continue` overwrites an existing controller deployment. Ask unless overwrite was explicitly approved.
- Success dialog says the app is deployed and offers `Open in browser`.

Validated browser-open route:

- Click `Open in browser` from the success dialog.
- Chrome opens `https://127.0.0.1:80/fileservice/$HOME/WebApps/Palletizing/index.html?nocache=<uuid>`.
- If Chrome shows the native login dialog `Anmelden`, use username `Default User` and ask the operator for the current-session password.
- Do not commit plaintext passwords. If a reusable local credential is needed, keep it in ignored local environment such as `.env` or `.env.local`.
- Successful browser evidence includes Chrome title `Palletizing - Google Chrome` and visible labels `Palletizing`, `Production`, `Currently Palletizing`, `demo_pallet`, `Current layer 2/8`, `Total boxes placed 11/88`, and `88 % Remaining`.

## RobotStudio Quick Route

RobotStudio executable:

```text
C:\Program Files (x86)\ABB\RobotStudio 2025\Bin\RobotStudio.exe
```

Validated open route:

- Start RobotStudio.
- Click `Item_BackstageTabOpen`.
- Select recent project `Palletize Template_new`.
- Click `Open`.

Success signals:

- window title: `Palletize Template_new - RobotStudio`
- project info/output references `GoFa10`
- status bar: `Controller status: 1/1`

Validated restart route:

- `&Controller`
- `CmdBarCtl_ControllerRestartWarm`
- confirmation dialog `Restart (Warmstart)`
- click `OK` only when explicitly requested
- wait for `Controller status: 1/1`

## FlexPendant Quick Route

Open from RobotStudio:

- `&Controller`
- `CmdBarCtl_LaunchVNext`

Expected window:

```text
VIRTUAL_CONTROLLER/GoFa10 - ABB Robotics FlexPendant
```

Process:

```text
ApplicationFrameHost.exe
```

The helper allowlist includes this process, but future automation should still verify the window title contains `ABB Robotics FlexPendant`.

Validated app list includes:

- `Palletizing`
- `PalletizingOld`

To open `Palletizing`, click the containing `GridViewItem` tile. The text label alone may have a zero-sized UIA rectangle and may not open the app.

What the opened Palletizing app exposes:

- `Production`
- `Tuning`
- `Recipe configuration`
- `Pattern builder`
- `Palletizing | Production`
- `Currently Palletizing`
- `demo_pallet`
- `Abort pallet`
- `Start new pallet`
- `Stop immediately`
- `Resume`
- `Pallet 1 Active`
- `Pallet 2 Full`
- `Pattern name: demo_pattern_2`
- `Current layer 2/8`
- `Total boxes placed 11/88`
- `88 % Remaining`

## Safety Rules

Always stop and ask before:

- overwriting deployments unless already approved for that task;
- deleting/replacing AppStudio or RobotStudio projects;
- restarting a controller unless explicitly requested;
- pressing `Abort pallet`, `Start new pallet`, `Stop immediately`, `Resume`, or pallet-state controls;
- changing Motors On/Off, jogging, calibration, SafeMove, or write access;
- entering credentials not provided in the active task.

Safe by default:

- observing UI trees;
- opening existing projects;
- navigating read-only views;
- launching FlexPendant;
- opening deployed apps for inspection;
- documenting findings.

## Current Proven Capability

A Codex thread can now, with supervision:

- operate AppStudio enough to open/create projects and deploy;
- operate RobotStudio enough to open a project, confirm a controller, and restart it when asked;
- launch FlexPendant and open the Palletizing app;
- inspect deployed Palletizing runtime text without screenshots;
- update the helper/docs and push changes to GitHub.

## What Is Still Missing

The next engineering step is to turn these proven manual routes into reusable scenario runners:

- `appstudio_full_journey.py`
- `robotstudio_open_project.py`
- `robotstudio_restart_controller.py`
- `flexpendant_open_app.py`
- JSON run reports under an ignored `runs/` folder

Those runners should require explicit flags for risky actions such as overwrite, restart, and runtime controls.
