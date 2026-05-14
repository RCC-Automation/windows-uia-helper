import hashlib
from typing import Any, Dict, Iterable, List, Optional, Tuple

from pywinauto import Desktop, keyboard
from pywinauto.application import Application
from pywinauto.controls.uiawrapper import UIAWrapper
from pywinauto.findwindows import ElementNotFoundError
import win32gui

from .element_cache import ElementCache
from .models import ElementInfo, ElementSummary, WindowInfo
from .safety import (
    SafetyError,
    assert_action_allowed,
    assert_hotkey_allowed,
    assert_not_risky,
    assert_process_allowed,
)


class UIAServiceError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


INTERACTIVE_CONTROL_TYPES = {
    "Button",
    "CheckBox",
    "ComboBox",
    "Edit",
    "Hyperlink",
    "ListItem",
    "MenuItem",
    "RadioButton",
    "Slider",
    "TabItem",
    "TreeItem",
}
TEXT_CONTROL_TYPES = {"Text", "Document"}
PATTERN_BY_ACTION = {
    "invoke": "invoke",
    "select": "select",
    "expand": "expand",
    "collapse": "collapse",
    "toggle": "toggle",
    "scroll_into_view": "scroll_into_view",
}


class UIAService:
    def __init__(self) -> None:
        self.desktop = Desktop(backend="uia")
        self.cache = ElementCache()

    def health(self) -> Dict[str, Any]:
        return {"ok": True, "backend": "uia", "screenshot_dependency": False}

    def list_windows(self) -> List[WindowInfo]:
        active_handle = self._active_handle()
        windows: List[WindowInfo] = []
        for window in self.desktop.windows(visible_only=True):
            info = self._window_info(window, active_handle)
            if info.title:
                windows.append(info)
        return windows

    def active_window(self) -> Dict[str, Any]:
        window = self._active_window()
        active_handle = self._active_handle()
        info = self._window_info(window, active_handle)
        self._check_window_allowed(info)
        elements = self._descendants(window)
        focus = self._safe_focus_element()
        return {
            "window": info.dict(),
            "summary": {
                "title": info.title,
                "control_count": len(elements),
                "focus_element": focus,
            },
        }

    def tree(
        self,
        handle: Optional[int] = None,
        max_depth: int = 5,
        include_invisible: bool = False,
    ) -> ElementInfo:
        window = self._window_by_handle(handle) if handle else self._active_window()
        info = self._window_info(window, self._active_handle())
        self._check_window_allowed(info)
        self.cache.clear()
        return self._element_info(window, "0", 0, max_depth, include_invisible)

    def observe(self, max_depth: int = 5) -> Dict[str, Any]:
        window = self._active_window()
        info = self._window_info(window, self._active_handle())
        self._check_window_allowed(info)
        self.cache.clear()
        elements = self._flatten_tree(self._element_info(window, "0", 0, max_depth, False))
        interactive = []
        text = []
        for element in elements:
            item = {
                "id": element.id,
                "label": element.name,
                "role": element.control_type,
                "enabled": element.enabled,
                "rect": element.rect,
            }
            if element.control_type in INTERACTIVE_CONTROL_TYPES and element.enabled and element.visible:
                interactive.append(item)
            elif element.control_type in TEXT_CONTROL_TYPES and element.name:
                text.append({"label": element.name, "role": element.control_type, "rect": element.rect})
        return {
            "active_window": {"title": info.title, "handle": info.handle},
            "focus": self._safe_focus_element(),
            "interactive_elements": interactive[:200],
            "text_elements": text[:200],
        }

    def find(
        self,
        handle: Optional[int],
        name: Optional[str],
        control_type: Optional[str],
        automation_id: Optional[str],
        contains: bool,
    ) -> List[ElementSummary]:
        window = self._window_by_handle(handle) if handle else self._active_window()
        info = self._window_info(window, self._active_handle())
        self._check_window_allowed(info)
        self.cache.clear()
        root = self._element_info(window, "0", 0, 8, False)
        matches = []
        for element in self._flatten_tree(root):
            if self._element_matches(element, name, control_type, automation_id, contains):
                matches.append(
                    ElementSummary(
                        id=element.id,
                        name=element.name,
                        control_type=element.control_type,
                        rect=element.rect,
                        patterns=element.patterns,
                    )
                )
        return matches

    def action(self, element_id: str, action: str, confirm: bool = False) -> Dict[str, Any]:
        assert_action_allowed(action)
        cached = self.cache.get(element_id)
        if cached is None:
            raise UIAServiceError("ELEMENT_NOT_FOUND", f"Could not find element with id {element_id}.")
        assert_not_risky(cached.metadata.get("name", ""), confirm)
        wrapper = cached.wrapper
        if action == "focus":
            wrapper.set_focus()
        elif action in {"click", "double_click", "right_click"}:
            self._click(wrapper, action)
        else:
            self._pattern_action(wrapper, action)
        return {"action": action, "element_id": element_id}

    def type_text(self, element_id: str, text: str, clear_first: bool = True, confirm: bool = False) -> Dict[str, Any]:
        cached = self.cache.get(element_id)
        if cached is None:
            raise UIAServiceError("ELEMENT_NOT_FOUND", f"Could not find element with id {element_id}.")
        assert_not_risky(cached.metadata.get("name", ""), confirm)
        wrapper = cached.wrapper
        wrapper.set_focus()
        if "Value" in cached.metadata.get("patterns", []):
            value_pattern = wrapper.iface_value
            value_pattern.SetValue("" if clear_first else value_pattern.CurrentValue)
            if text:
                value_pattern.SetValue(text if clear_first else value_pattern.CurrentValue + text)
        else:
            if clear_first:
                keyboard.send_keys("^a{BACKSPACE}")
            keyboard.send_keys(text, with_spaces=True, pause=0.01)
        return {"action": "type", "element_id": element_id, "detail": {"characters": len(text)}}

    def hotkey(self, keys: Iterable[str]) -> Dict[str, Any]:
        normalized = assert_hotkey_allowed(keys)
        keyboard.send_keys(self._pywinauto_hotkey(normalized))
        return {"action": "hotkey", "detail": {"keys": normalized}}

    def _active_window(self) -> UIAWrapper:
        try:
            handle = self._active_handle()
            if not handle:
                raise UIAServiceError("WINDOW_NOT_FOUND", "No active window was found.")
            return self._window_by_handle(handle)
        except (ElementNotFoundError, UIAServiceError) as exc:
            raise UIAServiceError("WINDOW_NOT_FOUND", "No active window was found.") from exc

    def _active_handle(self) -> Optional[int]:
        try:
            handle = int(win32gui.GetForegroundWindow())
            return handle or None
        except Exception:
            return None

    def _window_by_handle(self, handle: Optional[int]) -> UIAWrapper:
        if handle is None:
            return self._active_window()
        try:
            app = Application(backend="uia").connect(handle=handle)
            return app.window(handle=handle)
        except Exception as exc:
            raise UIAServiceError("WINDOW_NOT_FOUND", f"Could not find window handle {handle}.") from exc

    def _window_info(self, window: UIAWrapper, active_handle: Optional[int]) -> WindowInfo:
        rect = window.rectangle()
        process_id = int(window.process_id())
        return WindowInfo(
            handle=int(window.handle),
            title=window.window_text() or "",
            process_id=process_id,
            process_name=self._process_name(process_id),
            class_name=window.class_name() or "",
            rect=[rect.left, rect.top, rect.right, rect.bottom],
            is_active=active_handle == int(window.handle),
        )

    def _process_name(self, process_id: int) -> Optional[str]:
        try:
            import psutil  # type: ignore

            return psutil.Process(process_id).name()
        except Exception:
            try:
                import win32process
                import win32gui

                handles: List[int] = []

                def callback(hwnd: int, _extra: Any) -> bool:
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    if pid == process_id:
                        handles.append(hwnd)
                        return False
                    return True

                win32gui.EnumWindows(callback, None)
            except Exception:
                return None
        return None

    def _check_window_allowed(self, info: WindowInfo) -> None:
        assert_process_allowed(info.process_name)

    def _descendants(self, window: UIAWrapper) -> List[UIAWrapper]:
        try:
            return list(window.descendants())
        except Exception:
            return []

    def _element_info(
        self,
        wrapper: UIAWrapper,
        path: str,
        depth: int,
        max_depth: int,
        include_invisible: bool,
    ) -> ElementInfo:
        rect_obj = wrapper.rectangle()
        visible = bool(wrapper.is_visible())
        element_id = self._element_id(wrapper, path)
        patterns = self._patterns(wrapper)
        metadata = {
            "name": wrapper.window_text() or "",
            "control_type": wrapper.element_info.control_type or "",
            "patterns": patterns,
        }
        self.cache.put(element_id, wrapper, metadata)
        children: List[ElementInfo] = []
        if depth < max_depth:
            try:
                child_wrappers = wrapper.children()
            except Exception:
                child_wrappers = []
            for index, child in enumerate(child_wrappers):
                try:
                    if include_invisible or child.is_visible():
                        children.append(
                            self._element_info(child, f"{path}.{index}", depth + 1, max_depth, include_invisible)
                        )
                except Exception:
                    continue
        return ElementInfo(
            id=element_id,
            name=metadata["name"],
            control_type=metadata["control_type"],
            automation_id=wrapper.element_info.automation_id or "",
            class_name=wrapper.class_name() or "",
            rect=[rect_obj.left, rect_obj.top, rect_obj.right, rect_obj.bottom],
            enabled=bool(wrapper.is_enabled()),
            visible=visible,
            focused=bool(wrapper.has_keyboard_focus()),
            patterns=patterns,
            children=children,
        )

    def _element_id(self, wrapper: UIAWrapper, path: str) -> str:
        raw = "|".join(
            [
                path,
                str(getattr(wrapper, "handle", "")),
                wrapper.window_text() or "",
                wrapper.element_info.control_type or "",
                wrapper.element_info.automation_id or "",
            ]
        )
        return hashlib.sha1(raw.encode("utf-8", errors="ignore")).hexdigest()[:16]

    def _patterns(self, wrapper: UIAWrapper) -> List[str]:
        checks: List[Tuple[str, str]] = [
            ("Invoke", "iface_invoke"),
            ("Value", "iface_value"),
            ("SelectionItem", "iface_selection_item"),
            ("ExpandCollapse", "iface_expand_collapse"),
            ("Toggle", "iface_toggle"),
            ("ScrollItem", "iface_scroll_item"),
        ]
        found = []
        for name, attr in checks:
            try:
                getattr(wrapper, attr)
                found.append(name)
            except Exception:
                continue
        return found

    def _flatten_tree(self, root: ElementInfo) -> List[ElementInfo]:
        items = [root]
        for child in root.children:
            items.extend(self._flatten_tree(child))
        return items

    def _element_matches(
        self,
        element: ElementInfo,
        name: Optional[str],
        control_type: Optional[str],
        automation_id: Optional[str],
        contains: bool,
    ) -> bool:
        if name:
            left = element.name.lower()
            right = name.lower()
            if contains:
                if right not in left:
                    return False
            elif left != right:
                return False
        if control_type and element.control_type.lower() != control_type.lower():
            return False
        if automation_id and element.automation_id.lower() != automation_id.lower():
            return False
        return True

    def _click(self, wrapper: UIAWrapper, action: str) -> None:
        if action == "click":
            wrapper.click_input()
        elif action == "double_click":
            wrapper.double_click_input()
        elif action == "right_click":
            wrapper.right_click_input()

    def _pattern_action(self, wrapper: UIAWrapper, action: str) -> None:
        if action == "invoke":
            try:
                wrapper.invoke()
                return
            except Exception:
                wrapper.click_input()
                return
        if action == "select":
            wrapper.select()
            return
        if action == "expand":
            wrapper.expand()
            return
        if action == "collapse":
            wrapper.collapse()
            return
        if action == "toggle":
            wrapper.toggle()
            return
        if action == "scroll_into_view":
            wrapper.scroll_into_view()
            return
        raise UIAServiceError("ACTION_NOT_SUPPORTED", f"Action '{action}' is not supported.")

    def _safe_focus_element(self) -> Optional[Dict[str, Any]]:
        try:
            focused = self.desktop.get_focus()
            info = self._element_info(focused, "focus", 0, 0, True)
            return info.dict()
        except Exception:
            return None

    def _pywinauto_hotkey(self, keys: List[str]) -> str:
        if len(keys) == 1:
            key = keys[0]
            return {"enter": "{ENTER}", "escape": "{ESC}", "tab": "{TAB}"}.get(key, key)
        mapping = {"ctrl": "^", "alt": "%", "shift": "+"}
        prefix = "".join(mapping.get(key, "") for key in keys[:-1])
        return prefix + keys[-1]
