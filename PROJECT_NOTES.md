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

## 2026-05-14 New Blank Project Creation Validation

Validated leaving an existing project and creating a new blank AppStudio project.

Route out of an open project:

- In the AppStudio WebView breadcrumb, click the middle project-name link in `Projects > <project name> > <web app name>`.
- For `Palletizing`, clicking the first `Palletizing` link after `Projects` returned to the front page.

New-project route:

- Click `New project`.
- In `Create a project`, click `Project with a blank web app`.
- The property form exposes default location `C:/Users/barru/Documents/AppStudio/Projects`, web app name `Webapp3`, `FlexPendant 1024 x 680 px`, `Enable compact screen`, `Web app logo`, tabs `Property` and `Language`, and buttons `Previous` and `Create`.
- Change `*Web app name` to a short name. The validation used `AITest01`.
- Click `Create`.
- AppStudio created `C:\Users\barru\Documents\AppStudio\Projects\AITest01`.
- Clicking the new `AITest01` project-card row opened the blank app designer.

Generated files observed:

- `AITest01.aspproj`
- `WebAppData.json`
- `WebAppData_mini.json`
- image defaults under `Assets/images`
- `Languages/en.json`
- scaffold folders `CFG`, `MOD`, and `CustomFunctions`

The opened blank designer showed breadcrumb `Projects > AITest01 > AITest01`, visible `Deploy`, `UI designer`, `Function`, `Translation`, `Component`, `Structure`, `Appearance`, `Behavior`, and default starter content such as `This is a Text` and `Button`.

## 2026-05-14 RobotStudio Open Recent Project Validation

Validated RobotStudio startup from scratch and opening an existing recent project.

Executable:

```text
C:\Program Files (x86)\ABB\RobotStudio 2025\Bin\RobotStudio.exe
```

Startup state:

- Window title: `RobotStudio`
- UIA exposes `Backstage_New`, `Item_BackstageTabOpen`, and ribbon tabs.

Open route:

- Click `Item_BackstageTabOpen`.
- `Backstage_Open` appears.
- Recent projects list exposed `Palletize Template_new` and `Project1`.
- Select `Palletize Template_new`.
- Project info pane shows `Open`, location `C:\Users\barru\Documents\RobotStudio\Projects`, virtual controller `GoFa10`, and RobotWare `7.21.0`.
- Click `Open`.

Success evidence:

- Window title changed to `Palletize Template_new - RobotStudio`.
- Station tree showed `/Palletize Template_new*` and mechanisms/components.
- Status bar showed `Controller status: 1/1`.
- Output showed `GoFa10 (Station)` events including system restart, program started, user logged on, Motors On, and Motors Off.

Conclusion: the recent-project route is enough for a future AI workflow to start RobotStudio, open the expected station, and confirm that one virtual controller is loaded before AppStudio attempts controller login/deployment.

## 2026-05-14 RobotStudio Virtual Controller Restart Validation

Validated warm restart route for the loaded `Palletize Template_new` project and `GoFa10` virtual controller.

Route:

- Click RobotStudio ribbon tab `&Controller`.
- In `Controller Tools`, invoke `CmdBarCtl_ControllerRestartWarm`.
- RobotStudio shows `Restart (Warmstart)`.
- Confirmation text: `The controller will be restarted. The state is saved and any changed configuration parameters will be activated after the restart.`
- Click `OK` only when restart is explicitly approved.

Post-restart validation:

- No confirmation dialog remained.
- Window title remained `Palletize Template_new - RobotStudio`.
- Status bar showed `Controller status: 1/1`.
- Output pane exposed `GoFa10 (Station)` controller events, including `10045 - System restarted`, Motors On/Off, and safety-warning messages.

Safety note: warm restart affects the virtual controller runtime state and may activate changed configuration parameters. Do not run it unless explicitly requested by the operator or a scenario has an explicit `allow_restart=true` flag.

## 2026-05-15 FlexPendant Launch And Palletizing App Validation

Validated opening FlexPendant from RobotStudio and launching the Palletizing app.

RobotStudio route:

- Open project `Palletize Template_new`.
- Click ribbon tab `&Controller`.
- In the FlexPendant group, click `CmdBarCtl_LaunchVNext`.

FlexPendant window:

- title: `VIRTUAL_CONTROLLER/GoFa10 - ABB Robotics FlexPendant`
- Windows process: `ApplicationFrameHost.exe`
- helper allowlist now includes `applicationframehost.exe`.

FlexPendant home screen UIA exposed:

- `ABB Robotics`
- `Messages`
- `Event log`
- `Motors_off`
- `ROB_1`
- `Axis 1-3`
- `Write access is held by: RobAPI2-Client,`
- app tiles including `Code`, `Program Data`, `Jog`, `Settings`, `I/O`, `Operate`, `Calibrate`, `File Explorer`, `SafeMove`, `Controller Software`, `ASI Setting`, `Wizard`, `Palletizing`, and `PalletizingOld`.

Opening `Palletizing`:

- Clicking the `Palletizing` text label alone did not open it because the label had a zero-sized UIA rectangle.
- Clicking the containing `GridViewItem` app tile opened the app. In this run it was zero-based tile index `12`, but future automation should map label to containing tile rather than hard-code the index.

Opened Palletizing app:

- exposed as embedded WebView2/Chromium inside FlexPendant;
- UIA wrappers included `Microsoft.UI.Xaml.Controls.WebView2`, `Chrome_WidgetWin_1`, `Palletizing - Web content`, and `Document: Palletizing`;
- visible app content included `Production`, `Tuning`, `Recipe configuration`, `Pattern builder`, `Palletizing | Production`, `Currently Palletizing`, `demo_pallet`, `Abort pallet`, `Start new pallet`, `Stop immediately`, `Resume`, `Pallet status`, `Pallet 1 Active`, `Pallet 2 Full`, `Pattern name: demo_pattern_2`, `Current layer 2/8`, `Total boxes placed 11/88`, and `88 % Remaining`.

Safety note: FlexPendant is a real runtime surface. Reading and navigating is safe, but do not click runtime-affecting controls without explicit approval.
