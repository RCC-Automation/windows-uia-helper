from typing import Optional

from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse

from .chromium_accessibility import ChromiumAccessibilityError, ChromiumAccessibilityService
from .models import ActionRequest, ChromiumFindRequest, ChromiumPageRequest, FindRequest, HotkeyRequest, TypeRequest
from .safety import SafetyError
from .uia_service import UIAService, UIAServiceError


app = FastAPI(
    title="Windows UI Automation Helper",
    description="Localhost-only Windows UI Automation JSON helper. Screenshots are not used.",
    version="0.1.0",
)
service = UIAService()
chromium_service = ChromiumAccessibilityService()


@app.exception_handler(UIAServiceError)
async def handle_uia_error(_request, exc: UIAServiceError):
    return JSONResponse(status_code=400, content={"ok": False, "error": exc.code, "message": exc.message})


@app.exception_handler(SafetyError)
async def handle_safety_error(_request, exc: SafetyError):
    return JSONResponse(status_code=403, content={"ok": False, "error": exc.code, "message": exc.message})


@app.exception_handler(ChromiumAccessibilityError)
async def handle_chromium_error(_request, exc: ChromiumAccessibilityError):
    return JSONResponse(status_code=400, content={"ok": False, "error": exc.code, "message": exc.message})


@app.get("/health")
def health():
    return service.health()


@app.get("/windows")
def windows():
    return {"windows": [window.dict() for window in service.list_windows()]}


@app.get("/active-window")
def active_window():
    return service.active_window()


@app.get("/tree")
def tree(
    handle: Optional[int] = None,
    max_depth: int = Query(default=5, ge=0, le=10),
    include_invisible: bool = False,
):
    return service.tree(handle=handle, max_depth=max_depth, include_invisible=include_invisible).dict()


@app.get("/observe")
def observe(max_depth: int = Query(default=5, ge=0, le=10)):
    return service.observe(max_depth=max_depth)


@app.post("/find")
def find(request: FindRequest):
    matches = service.find(
        handle=request.handle,
        name=request.name,
        control_type=request.control_type,
        automation_id=request.automation_id,
        contains=request.contains,
    )
    return {"matches": [match.dict() for match in matches]}


@app.post("/action")
def action(request: ActionRequest):
    return {"ok": True, **service.action(request.element_id, request.action, confirm=request.confirm)}


@app.post("/type")
def type_text(request: TypeRequest):
    return {"ok": True, **service.type_text(request.element_id, request.text, request.clear_first, request.confirm)}


@app.post("/hotkey")
def hotkey(request: HotkeyRequest):
    return {"ok": True, **service.hotkey(request.keys)}


@app.get("/chromium/status")
def chromium_status(host: str = "127.0.0.1", port: int = 9222):
    return chromium_service.status(host=host, port=port)


@app.get("/chromium/pages")
def chromium_pages(host: str = "127.0.0.1", port: int = 9222):
    return {"pages": chromium_service.pages(host=host, port=port)}


@app.post("/chromium/accessibility")
def chromium_accessibility(request: ChromiumPageRequest):
    return chromium_service.accessibility_tree(host=request.host, port=request.port, page_id=request.page_id)


@app.post("/chromium/find")
def chromium_find(request: ChromiumFindRequest):
    return chromium_service.find(
        host=request.host,
        port=request.port,
        page_id=request.page_id,
        name=request.name,
        role=request.role,
        contains=request.contains,
    )
