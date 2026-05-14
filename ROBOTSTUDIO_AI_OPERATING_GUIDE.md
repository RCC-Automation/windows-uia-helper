# RobotStudio AI Operating Guide

This guide documents the validated RobotStudio startup and open-existing-project route for future Codex/AppStudio automation work.

## Purpose

RobotStudio is needed alongside AppStudio when AppStudio deployments must connect to a RobotStudio virtual controller. Future AI threads should be able to start RobotStudio, open an existing project from the recent-project list, and confirm that the project and virtual controller are loaded before AppStudio connects or deploys.

## Executable

Validated RobotStudio executable:

```text
C:\Program Files (x86)\ABB\RobotStudio 2025\Bin\RobotStudio.exe
```

Launch command:

```powershell
Start-Process -FilePath "C:\Program Files (x86)\ABB\RobotStudio 2025\Bin\RobotStudio.exe"
```

## Startup State

When started from scratch, RobotStudio opened with window title:

```text
RobotStudio
```

The UI Automation tree exposed the startup Backstage/New page:

- `Backstage`
- `Backstage_New`
- `Item_BackstageTabNew`
- `Item_BackstageTabOpen`
- ribbon tabs such as `&File`, `&Home`, `&Modeling`, `&Simulation`, `&Controller`, `&RAPID`, `&Add-Ins`

## Open An Existing Recent Project

Validated route:

1. Start RobotStudio.
2. In the Backstage area, click the custom UIA element:

```text
Item_BackstageTabOpen
```

3. RobotStudio switches to:

```text
Backstage_Open
```

4. The left Open page exposes:

- `CmdList_BackstageOpenRecent`
- `CmdList_BackstageOpenCloud`
- `CmdList_BackstageOpenLocal`
- `CmdList_FileOpen`
- `CmdList_BackstageOpenSample`

5. The recent-project list exposed local project cards:

- `Palletize Template_new`
- `Project1`

6. Select the desired project card. For the validated run, select:

```text
Palletize Template_new
```

7. RobotStudio shows a project information pane with:

- project name: `Palletize Template_new`
- type: `Project`
- button: `Open`
- location: `C:\Users\barru\Documents\RobotStudio\Projects`
- virtual controller: `GoFa10`
- RobotWare: `7.21.0`

8. Click the `Open` button.

## Success Signals

After opening the project, RobotStudio window title changed to:

```text
Palletize Template_new - RobotStudio
```

The UI tree exposed station/project content such as:

- document tab: `DocumentTab_Palletize Template_new:View1`
- station tree root: `/Palletize Template_new*`
- mechanisms/components such as `CRB15000_10_152__01`, `Vacuum gripper`, `Roller Conveyor`, `SC Gripper V2`, pallets, slipsheets, and lift-kit entries
- output tab: `DockTab_Output`

Controller validation signals:

- Status bar pane:

```text
Controller status: 1/1
```

- Output messages referencing the virtual controller:

```text
GoFa10 (Station): 10045 - System restarted
GoFa10 (Station): 10010 - Motors Off state
GoFa10 (Station): 10017 - Automatic mode confirmed
GoFa10 (Station): 10155 - Program restarted
GoFa10 (Station): 10150 - Program started
GoFa10 (Station): 10400 - User Admin logged on
GoFa10 (Station): 10011 - Motors On state
```

In the validated run, the latest output also included `Motors Off state`. Treat this as "controller loaded and reporting state", not necessarily "robot is ready to move".

## Safety Rules

Opening an existing recent project is safe.

Stop and ask before:

- creating or deleting RobotStudio projects;
- saving changes to a project;
- synchronizing RAPID/controller content;
- starting, stopping, resetting, or jogging the robot;
- changing Motors On/Off state;
- changing virtual controller configuration;
- dismissing safety dialogs or automatic-mode warnings.

For AppStudio deployment workflows, the minimum RobotStudio validation needed before AppStudio connects is:

1. RobotStudio title shows the expected project.
2. A virtual controller is listed in the project info or output.
3. Status bar shows `Controller status: 1/1`, or equivalent evidence that one controller is loaded.

## Missing Capabilities To Implement Next

- Add a reusable RobotStudio scenario runner that:
  - starts RobotStudio if needed;
  - clicks `Item_BackstageTabOpen`;
  - selects a recent project by visible name;
  - clicks `Open`;
  - waits for the title to become `<project> - RobotStudio`;
  - extracts controller status and output messages into JSON.

- Add project disambiguation:
  - list all recent projects;
  - report location, size, last edited time, and virtual controllers;
  - require operator confirmation if more than one plausible project matches.

- Add controller readiness checks:
  - detect `Controller status: 1/1`;
  - extract controller name and RobotWare version from the info pane when available;
  - classify output messages into loaded/running/stopped/motors-on/motors-off/safety-stop.

- Investigate RobotStudio APIs or command-line options for opening a project directly, but keep the UIA recent-project route as the proven fallback.
