import json
import subprocess
import time
from typing import Any, Dict, List, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


BASE_URL = "http://127.0.0.1:8765"
APPSTUDIO_EXE = r"C:\Program Files (x86)\ABB\AppStudio\AppStudio.Desktop.exe"
DEVTOOLS_PORTS = [9222, 9223, 9333, 9515]


def get(path: str, query: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    url = BASE_URL + path
    if query:
        url += "?" + urlencode(query)
    with urlopen(url, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


def post(path: str, body: Dict[str, Any]) -> Dict[str, Any]:
    request = Request(
        BASE_URL + path,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def try_get(path: str, query: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    try:
        return get(path, query)
    except (HTTPError, URLError, TimeoutError) as exc:
        return {"ok": False, "error": type(exc).__name__, "message": str(exc)}


def appstudio_windows() -> List[Dict[str, Any]]:
    windows = get("/windows").get("windows", [])
    return [window for window in windows if window.get("title") == "AppStudio"]


def start_appstudio_if_needed() -> Optional[int]:
    windows = appstudio_windows()
    if windows:
        return windows[0]["handle"]
    subprocess.Popen([APPSTUDIO_EXE])
    for _ in range(30):
        time.sleep(1)
        windows = appstudio_windows()
        if windows:
            return windows[0]["handle"]
    return None


def main() -> None:
    print("Health:")
    print(json.dumps(get("/health"), indent=2))

    handle = start_appstudio_if_needed()
    if handle is None:
        raise RuntimeError("AppStudio did not appear as a visible top-level window.")

    print(f"AppStudio handle: {handle}")

    print("UIA shell probes:")
    shell_queries = [
        {"name": "Connect to controller", "contains": True},
        {"automation_id": "ProjectButton"},
        {"automation_id": "ComponentButton"},
        {"automation_id": "CloudButton"},
        {"automation_id": "SettingsButton"},
    ]
    for query in shell_queries:
        result = post("/find", {"handle": handle, **query})
        print(json.dumps({"query": query, "matches": result.get("matches", [])[:5]}, indent=2))

    print("Chromium DevTools probes:")
    reachable_ports = []
    for port in DEVTOOLS_PORTS:
        status = try_get("/chromium/status", {"port": port})
        print(json.dumps({"port": port, "status": status}, indent=2))
        if status.get("ok"):
            reachable_ports.append(port)

    for port in reachable_ports:
        print(f"Chromium pages on port {port}:")
        print(json.dumps(try_get("/chromium/pages", {"port": port}), indent=2)[:8000])
        print(f"Accessibility search for Projects on port {port}:")
        print(
            json.dumps(
                post(
                    "/chromium/find",
                    {"host": "127.0.0.1", "port": port, "name": "Projects", "contains": True},
                ),
                indent=2,
            )[:8000]
        )

    if not reachable_ports:
        print(
            "No Chromium DevTools endpoint was reachable on the common ports. "
            "AppStudio may need a WebView2/Chromium remote-debugging launch option."
        )


if __name__ == "__main__":
    main()
