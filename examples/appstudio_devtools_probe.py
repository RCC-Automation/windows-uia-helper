import json
import os
import subprocess
import time
from typing import Any, Dict
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen


BASE_URL = "http://127.0.0.1:8765"
APPSTUDIO_EXE = r"C:\Program Files (x86)\ABB\AppStudio\AppStudio.Desktop.exe"
DEVTOOLS_PORT = 9222


def get(path: str, query: Dict[str, Any], timeout: int = 3) -> Dict[str, Any]:
    url = BASE_URL + path
    if query:
        url += "?" + urlencode(query)
    with urlopen(url, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def wait_for_devtools(port: int, timeout_seconds: int = 12) -> Dict[str, Any]:
    last_status: Dict[str, Any] = {}
    for _ in range(timeout_seconds):
        try:
            status = get("/chromium/status", {"port": port}, timeout=3)
        except (HTTPError, URLError, TimeoutError) as exc:
            status = {"ok": False, "error": type(exc).__name__, "message": str(exc)}
        last_status = status
        if status.get("ok"):
            return status
        time.sleep(1)
    return last_status


def main() -> None:
    env = os.environ.copy()
    env["WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS"] = f"--remote-debugging-port={DEVTOOLS_PORT}"

    print(f"Launching AppStudio with WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS={env['WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS']}")
    subprocess.Popen([APPSTUDIO_EXE], env=env)

    print("Waiting for DevTools endpoint...")
    status = wait_for_devtools(DEVTOOLS_PORT)
    print(json.dumps(status, indent=2))

    if not status.get("ok"):
        print(
            "DevTools did not become reachable. If AppStudio is already running, fully close it and rerun this probe; "
            "single-instance apps often ignore environment changes after the first process starts."
        )


if __name__ == "__main__":
    main()
