from typing import Iterable, List, Optional


class SafetyError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


ALLOWED_PROCESSES = {
    "notepad.exe",
    "calc.exe",
    "calculatorapp.exe",
    "robotstudio.exe",
    "appstudio.desktop.exe",
}
ALLOWED_ACTIONS = {
    "focus",
    "invoke",
    "click",
    "double_click",
    "right_click",
    "select",
    "expand",
    "collapse",
    "toggle",
    "scroll_into_view",
    "type",
    "hotkey",
}
RISKY_WORDS = {
    "delete",
    "remove",
    "send",
    "pay",
    "submit",
    "install",
    "uninstall",
    "overwrite",
    "password",
    "credential",
    "close",
}
ALLOWED_HOTKEYS = {
    ("ctrl", "s"),
    ("ctrl", "c"),
    ("ctrl", "v"),
    ("ctrl", "f"),
    ("enter",),
    ("escape",),
    ("tab",),
}


def normalize_process_name(name: Optional[str]) -> str:
    return (name or "").strip().lower()


def assert_process_allowed(process_name: Optional[str]) -> None:
    normalized = normalize_process_name(process_name)
    if normalized and normalized not in ALLOWED_PROCESSES:
        raise SafetyError(
            "ACCESS_DENIED",
            f"Process '{process_name}' is not in the allowed_processes list.",
        )


def assert_action_allowed(action: str) -> None:
    if action not in ALLOWED_ACTIONS:
        raise SafetyError("ACTION_NOT_SUPPORTED", f"Action '{action}' is not allowed.")


def assert_not_risky(label: str, confirm: bool) -> None:
    lowered = (label or "").lower()
    if not confirm and any(word in lowered for word in RISKY_WORDS):
        raise SafetyError(
            "RISKY_ACTION_REQUIRES_CONFIRMATION",
            f"Element '{label}' looks risky and requires confirm=true.",
        )


def normalize_hotkey(keys: Iterable[str]) -> List[str]:
    return [key.strip().lower() for key in keys if key and key.strip()]


def assert_hotkey_allowed(keys: Iterable[str]) -> List[str]:
    normalized = normalize_hotkey(keys)
    combo = tuple(normalized)
    if combo not in ALLOWED_HOTKEYS:
        raise SafetyError("ACTION_NOT_SUPPORTED", f"Hotkey '{'+'.join(normalized)}' is not allowed.")
    return normalized
