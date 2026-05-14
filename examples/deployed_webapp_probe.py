import argparse
import json
import subprocess
import tempfile
import time
from itertools import count
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.request import urlopen

import websocket


DEFAULT_URL = "https://127.0.0.1:80/fileservice/$HOME/WebApps/Palletizing/index.html"


class CdpPage:
    def __init__(self, websocket_url: str) -> None:
        self._ws = websocket.create_connection(websocket_url, timeout=10, suppress_origin=True)
        self._ids = count(1)

    def close(self) -> None:
        self._ws.close()

    def call(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        request_id = next(self._ids)
        self._ws.send(json.dumps({"id": request_id, "method": method, "params": params or {}}))
        while True:
            message = json.loads(self._ws.recv())
            if message.get("id") != request_id:
                continue
            if "error" in message:
                raise RuntimeError(f"{method}: {message['error']}")
            return message.get("result", {})

    def evaluate(self, expression: str) -> Any:
        result = self.call(
            "Runtime.evaluate",
            {"expression": expression, "returnByValue": True, "awaitPromise": True},
        )
        return result.get("result", {}).get("value")


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe an AppStudio deployed web app through Chrome DevTools.")
    parser.add_argument("--chrome", default=r"C:\Program Files\Google\Chrome\Application\chrome.exe")
    parser.add_argument("--port", type=int, default=9333)
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--username", default="Default User")
    parser.add_argument("--password", default=None)
    parser.add_argument("--keep-open", action="store_true")
    args = parser.parse_args()

    chrome = Path(args.chrome)
    if not chrome.exists():
        chrome = Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe")
    if not chrome.exists():
        raise SystemExit("Chrome executable was not found.")
    if not args.password:
        raise SystemExit("Pass --password with the controller web app password.")

    profile_dir = Path(tempfile.gettempdir()) / "appstudio-deployed-cdp-profile"
    profile_dir.mkdir(parents=True, exist_ok=True)
    subprocess.Popen(
        [
            str(chrome),
            f"--remote-debugging-port={args.port}",
            f"--remote-allow-origins=http://127.0.0.1:{args.port}",
            "--no-first-run",
            "--no-default-browser-check",
            f"--user-data-dir={profile_dir}",
            "about:blank",
        ]
    )
    time.sleep(3)

    pages = json.loads(urlopen(f"http://127.0.0.1:{args.port}/json", timeout=3).read().decode("utf-8"))
    page = next(item for item in pages if item.get("type") == "page" and item.get("webSocketDebuggerUrl"))
    cdp = CdpPage(page["webSocketDebuggerUrl"])
    try:
        cdp.call("Page.enable")
        cdp.call("Runtime.enable")
        cdp.call("Security.enable")
        cdp.call("Security.setIgnoreCertificateErrors", {"ignore": True})

        auth_url = args.url.replace("https://", f"https://{args.username.replace(' ', '%20')}:{args.password}@")
        cdp.call("Page.navigate", {"url": auth_url})
        time.sleep(8)

        summary = cdp.evaluate(
            """({
                title: document.title,
                url: location.href,
                text: document.body ? document.body.innerText.slice(0, 5000) : "",
                menuItems: [...document.querySelectorAll(".fp-components-hamburgermenu-a-menu__button")]
                    .map(e => (e.innerText || "").trim())
                    .filter(Boolean)
            })"""
        )
        print(json.dumps(summary, indent=2))
    finally:
        cdp.close()
        if not args.keep_open:
            # Leave Chrome cleanup to the operator by default in exploratory sessions.
            pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
