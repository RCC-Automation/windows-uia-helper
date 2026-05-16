# FlexPendant AI Operating Guide

This guide documents how a future Codex/AppStudio automation thread can open ABB Robotics FlexPendant from RobotStudio, navigate to deployed AppStudio applications, and use FlexPendant as a validation surface.

## Why FlexPendant Matters

FlexPendant is closer to the real operator experience than a desktop browser. It is useful for validating AppStudio projects because:

- it runs against the RobotStudio virtual controller;
- it shows the controller shell state, including motors/status/write-access indicators;
- it hosts deployed AppStudio web apps in the teach-pendant environment;
- its UI is accessible through Windows UI Automation;
- deployed AppStudio app content is visible through UIA without screenshots;
- it can validate whether the controller-side deployment is actually available from the pendant app list.

Use FlexPendant when the goal is to validate the deployed operator workflow, not only the browser-rendered web app.

## Prerequisites

RobotStudio should already have the relevant project open and the virtual controller loaded.

Validated project:

```text
Palletize Template_new
```

Validated controller:

```text
GoFa10
```

RobotStudio readiness signals:

- window title includes `Palletize Template_new - RobotStudio`;
- status bar shows `Controller status: 1/1`;
- output or project info references `GoFa10`.

## Open FlexPendant

From RobotStudio:

1. Click the ribbon tab:

```text
&Controller
```

2. In the Controller ribbon, locate the FlexPendant controls:

```text
SplitButton: CmdBarSplitCtl_FlexPendantGallery
Button: CmdBarCtl_LaunchVNext
MenuItem: CmdBarCtl_FlexPendantGallery
```

3. Click:

```text
CmdBarCtl_LaunchVNext
```

4. Wait for a separate Windows app window:

```text
VIRTUAL_CONTROLLER/GoFa10 - ABB Robotics FlexPendant
```

## Helper Support

FlexPendant runs as a packaged Windows app hosted by:

```text
ApplicationFrameHost.exe
```

The helper allowlist includes:

```text
applicationframehost.exe
```

That allows the Windows UI Automation wrapper to inspect and act on the FlexPendant window. Because `ApplicationFrameHost.exe` can host other Windows apps too, future higher-level automation should additionally validate the active window title contains:

```text
ABB Robotics FlexPendant
```

## Home Screen

The FlexPendant home screen exposes these controller/status elements through UIA:

- `ABB Robotics`
- `Messages`
- `Event log`
- `Motors_off`
- `100%`
- `ROB_1`
- `Axis 1-3`
- `Write access is held by: RobAPI2-Client,`
- `VIRTUAL_CONTROLLER/GoFa10`
- `Home`

The app tiles are UIA `ListItem` controls with class:

```text
GridViewItem
```

Observed apps:

- `Code`
- `Program Data`
- `Jog`
- `Settings`
- `I/O`
- `Operate`
- `Calibrate`
- `File Explorer`
- `SafeMove`
- `Controller Software`
- `ASI Setting`
- `Wizard`
- `Palletizing`
- `PalletizingOld`

## Open A Deployed App

For the Palletizing validation:

1. Focus the FlexPendant window.
2. Find the app tile label:

```text
Palletizing
```

3. Do not rely on clicking the text node alone. In the validation run, the `Palletizing` text node had a zero-sized UIA rectangle and did not open the app.
4. Click the containing `GridViewItem` app tile.

In the validation run, `Palletizing` was the zero-based tile index `12` among `MainFrameApp.Model.AppModuleInfo` list items, but this should be treated only as a fallback. A durable implementation should map labels to their containing app tiles.

## Opened Palletizing App

After opening `Palletizing`, FlexPendant showed an embedded WebView2/Chromium host.

Observed wrappers:

- `Microsoft.UI.Xaml.Controls.WebView2`
- `Chrome_WidgetWin_1`
- `Palletizing - Web content`
- `BrowserRootView`
- `Document: Palletizing`

Important validation rule:

- Do not treat the bottom app-strip entry named `Palletizing` as proof that the app content is open.
- The successful state is the embedded browser/document surface:

```text
Chrome_WidgetWin_1: Palletizing
BrowserRootView: Palletizing - Web content
Document: Palletizing
```

- If the helper's normal `/find` call does not find `Production`, `Currently Palletizing`, or `Pattern name`, do not conclude that app switching failed. The app content may be deeper than the helper API's default traversal depth.
- Use a deeper UIA read from the same desktop context, or enhance the helper to search below `BrowserRootView` until it reaches `RootWebArea`.

Observed visible content:

- `Palletizing`
- `Production`
- `Tuning`
- `Recipe configuration`
- `Pattern builder`
- `Palletizing | Production`
- `Currently Palletizing`
- `demo_pallet`
- `Abort pallet`
- `Actions`
- `Start new pallet`
- `Stop immediately`
- `Resume`
- `Pallet status`
- `Pallet 1`
- `Active`
- `Pallet 2`
- `Full`
- `Click on Full (Palletizing done) for New (Ready to load) pallet status.`
- `Current layer`
- `Pattern name: demo_pattern_2`
- `Current layer 2/8`
- `Total boxes placed 11/88`
- `88 % Remaining`

Some controls are exposed as UIA `Group` elements with web component class names:

```text
fp-components-hamburgermenu-a-menu__button
fp-components-button
fp-components-button-disabled
fp-components-dropdown
```

This confirms that FlexPendant can be used to validate deployed AppStudio apps in the real controller/pendant host while still using structured UIA data.

## Navigation

The opened Palletizing app exposes the same high-level navigation as the deployed browser app:

- `Production`
- `Tuning`
- `Recipe configuration`
- `Pattern builder`

Safe navigation:

- switching between app views to inspect text/state;
- reading status values;
- reading disabled/enabled control labels.

Risky navigation/actions:

- `Abort pallet`
- `Start new pallet`
- `Stop immediately`
- `Resume`
- pallet status changes such as `Full`;
- Motors On/Off controls;
- jogging, calibration, SafeMove, or write-access actions.

Stop and ask before any runtime-affecting action.

## Validation Benefits

FlexPendant gives a stronger validation signal than a plain browser when the objective is AppStudio/controller integration:

- verifies RobotStudio virtual controller and FlexPendant can see the deployed app;
- validates the actual pendant shell and app list;
- exposes controller state next to the app;
- avoids browser-specific behavior that may differ from the teach pendant;
- still gives enough UIA structure for AI agents to inspect app content.

For development loops, a good validation sequence is:

1. Build or modify the AppStudio project.
2. Deploy to the controller from AppStudio.
3. Open RobotStudio and confirm controller `1/1`.
4. Launch FlexPendant.
5. Open the deployed app from the FlexPendant home screen.
6. Read visible app content through UIA.
7. Optionally navigate read-only app pages.
8. Record observations for the next implementation iteration.

## Known Limitations

- FlexPendant is hosted by `ApplicationFrameHost.exe`, a generic Windows host process. Do not treat every `ApplicationFrameHost.exe` window as safe; validate the title.
- Some labels may have zero-sized UIA rectangles. Click the containing tile/group, not only the text.
- The helper's default `/observe` depth may capture shell/breadcrumb text but miss deep WebView content. Use `/tree` with sufficient depth or direct UIA scripts when deeper inspection is required.
- A running-app strip entry at the bottom of FlexPendant can show `Palletizing` even while the normal helper search still misses the app's inner WebView text. Confirm `Document: Palletizing` and inner text such as `Palletizing | Production`, not only the strip entry.
- Runtime controls can change controller state. Reading is safe; acting needs explicit approval.

## Future Automation Work

Implement a reusable FlexPendant scenario runner:

- launch from RobotStudio via `CmdBarCtl_LaunchVNext`;
- wait for `ABB Robotics FlexPendant`;
- verify controller name in title;
- list home app tiles;
- map app label to containing `GridViewItem`;
- open named app;
- collect visible text and interactive elements;
- support read-only navigation;
- require explicit flags for runtime-affecting actions.
