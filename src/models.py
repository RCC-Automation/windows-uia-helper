from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


Rect = List[int]


class WindowInfo(BaseModel):
    handle: int
    title: str
    process_id: int
    process_name: Optional[str] = None
    class_name: str
    rect: Rect
    is_active: bool


class ElementInfo(BaseModel):
    id: str
    name: str
    control_type: str
    automation_id: str
    class_name: str
    rect: Rect
    enabled: bool
    visible: bool
    focused: bool
    patterns: List[str]
    children: List["ElementInfo"] = Field(default_factory=list)


ElementInfo.update_forward_refs()


class ElementSummary(BaseModel):
    id: str
    name: str
    control_type: str
    rect: Rect
    patterns: List[str]


class FindRequest(BaseModel):
    handle: Optional[int] = None
    name: Optional[str] = None
    control_type: Optional[str] = None
    automation_id: Optional[str] = None
    contains: bool = True


class FindResponse(BaseModel):
    matches: List[ElementSummary]


class ActionRequest(BaseModel):
    element_id: str
    action: str
    confirm: bool = False


class TypeRequest(BaseModel):
    element_id: str
    text: str
    clear_first: bool = True
    confirm: bool = False


class HotkeyRequest(BaseModel):
    keys: List[str]
    confirm: bool = False


class ChromiumPageRequest(BaseModel):
    host: str = "127.0.0.1"
    port: int = 9222
    page_id: Optional[str] = None


class ChromiumFindRequest(ChromiumPageRequest):
    name: Optional[str] = None
    role: Optional[str] = None
    contains: bool = True


class ChromiumClickRequest(ChromiumFindRequest):
    node_id: Optional[str] = None
    click_count: int = 1
    confirm: bool = False


class ErrorResponse(BaseModel):
    ok: bool = False
    error: str
    message: str


class ActionResponse(BaseModel):
    ok: bool = True
    action: str
    element_id: Optional[str] = None
    detail: Optional[Dict[str, Any]] = None
