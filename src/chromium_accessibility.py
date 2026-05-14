import json
import itertools
from typing import Any, Dict, List, Optional
from urllib.error import URLError
from urllib.request import urlopen


class ChromiumAccessibilityError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class ChromiumAccessibilityService:
    def status(self, host: str = "127.0.0.1", port: int = 9222) -> Dict[str, Any]:
        try:
            version = self._get_json(f"http://{host}:{port}/json/version", timeout=1)
            return {
                "ok": True,
                "host": host,
                "port": port,
                "browser": version.get("Browser"),
                "protocol_version": version.get("Protocol-Version"),
                "web_socket_debugger_url": version.get("webSocketDebuggerUrl"),
            }
        except Exception as exc:
            return {
                "ok": False,
                "host": host,
                "port": port,
                "error": "DEVTOOLS_NOT_REACHABLE",
                "message": str(exc),
            }

    def pages(self, host: str = "127.0.0.1", port: int = 9222) -> List[Dict[str, Any]]:
        pages = self._get_json(f"http://{host}:{port}/json", timeout=3)
        if not isinstance(pages, list):
            raise ChromiumAccessibilityError("DEVTOOLS_BAD_RESPONSE", "DevTools /json did not return a page list.")
        return [
            {
                "id": page.get("id"),
                "type": page.get("type"),
                "title": page.get("title"),
                "url": page.get("url"),
                "webSocketDebuggerUrl": page.get("webSocketDebuggerUrl"),
            }
            for page in pages
        ]

    def accessibility_tree(
        self,
        host: str = "127.0.0.1",
        port: int = 9222,
        page_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        page = self._select_page(host, port, page_id)
        websocket_url = page.get("webSocketDebuggerUrl")
        if not websocket_url:
            raise ChromiumAccessibilityError("DEVTOOLS_PAGE_NOT_DEBUGGABLE", "Selected page has no debugger URL.")
        result = self._cdp_call(websocket_url, "Accessibility.getFullAXTree", {})
        nodes = result.get("nodes", [])
        return {
            "page": {
                "id": page.get("id"),
                "title": page.get("title"),
                "url": page.get("url"),
            },
            "nodes": [self._compact_node(node) for node in nodes],
        }

    def find(
        self,
        host: str = "127.0.0.1",
        port: int = 9222,
        page_id: Optional[str] = None,
        name: Optional[str] = None,
        role: Optional[str] = None,
        contains: bool = True,
    ) -> Dict[str, Any]:
        tree = self.accessibility_tree(host=host, port=port, page_id=page_id)
        matches = []
        for node in tree["nodes"]:
            if self._matches(node, name=name, role=role, contains=contains):
                matches.append(node)
        return {"page": tree["page"], "matches": matches}

    def _select_page(self, host: str, port: int, page_id: Optional[str]) -> Dict[str, Any]:
        pages = self.pages(host, port)
        candidates = [page for page in pages if page.get("type") == "page" and page.get("webSocketDebuggerUrl")]
        if page_id:
            for page in pages:
                if page.get("id") == page_id:
                    return page
            raise ChromiumAccessibilityError("DEVTOOLS_PAGE_NOT_FOUND", f"No DevTools page with id {page_id}.")
        if not candidates:
            raise ChromiumAccessibilityError("DEVTOOLS_PAGE_NOT_FOUND", "No debuggable Chromium page was found.")
        return candidates[0]

    def _get_json(self, url: str, timeout: int) -> Any:
        try:
            with urlopen(url, timeout=timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except URLError as exc:
            raise ChromiumAccessibilityError("DEVTOOLS_NOT_REACHABLE", f"Could not reach {url}: {exc}") from exc

    def _cdp_call(self, websocket_url: str, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            import websocket  # type: ignore
        except ImportError as exc:
            raise ChromiumAccessibilityError(
                "WEBSOCKET_CLIENT_NOT_INSTALLED",
                "Install websocket-client to use Chromium accessibility endpoints.",
            ) from exc

        request_id = next(self._ids)
        ws = websocket.create_connection(websocket_url, timeout=10)
        try:
            ws.send(json.dumps({"id": request_id, "method": method, "params": params}))
            while True:
                message = json.loads(ws.recv())
                if message.get("id") != request_id:
                    continue
                if "error" in message:
                    raise ChromiumAccessibilityError("DEVTOOLS_COMMAND_FAILED", json.dumps(message["error"]))
                return message.get("result", {})
        finally:
            ws.close()

    _ids = itertools.count(1)

    def _compact_node(self, node: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "node_id": node.get("nodeId"),
            "ignored": node.get("ignored", False),
            "role": self._ax_value(node.get("role")),
            "name": self._ax_value(node.get("name")),
            "description": self._ax_value(node.get("description")),
            "value": self._ax_value(node.get("value")),
            "properties": self._compact_properties(node.get("properties", [])),
            "child_ids": node.get("childIds", []),
        }

    def _compact_properties(self, properties: List[Dict[str, Any]]) -> Dict[str, Any]:
        compact: Dict[str, Any] = {}
        for prop in properties:
            name = prop.get("name")
            if name:
                compact[name] = self._ax_value(prop.get("value"))
        return compact

    def _ax_value(self, payload: Optional[Dict[str, Any]]) -> Any:
        if not isinstance(payload, dict):
            return None
        return payload.get("value")

    def _matches(
        self,
        node: Dict[str, Any],
        name: Optional[str],
        role: Optional[str],
        contains: bool,
    ) -> bool:
        if name:
            left = str(node.get("name") or "").lower()
            right = name.lower()
            if contains:
                if right not in left:
                    return False
            elif left != right:
                return False
        if role and str(node.get("role") or "").lower() != role.lower():
            return False
        return True
