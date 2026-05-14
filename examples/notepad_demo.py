import json
import subprocess
import time
from typing import Any, Dict, List, Optional
from urllib.error import HTTPError
from urllib.request import Request, urlopen


BASE_URL = "http://127.0.0.1:8765"


def get(path: str) -> Dict[str, Any]:
    with urlopen(BASE_URL + path, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def post(path: str, body: Dict[str, Any]) -> Dict[str, Any]:
    data = json.dumps(body).encode("utf-8")
    request = Request(
        BASE_URL + path,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        payload = exc.read().decode("utf-8")
        raise RuntimeError(f"{path} failed: {payload}") from exc


def first_match(matches: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    return matches[0] if matches else None


def main() -> None:
    print("Starting Notepad...")
    subprocess.Popen(["notepad.exe"])
    time.sleep(1.5)

    print("Health:")
    print(json.dumps(get("/health"), indent=2))

    print("Observation:")
    observation = get("/observe")
    print(json.dumps(observation, indent=2))

    print("Finding editor element...")
    edit_matches = post("/find", {"control_type": "Edit", "contains": True})["matches"]
    document_matches = post("/find", {"control_type": "Document", "contains": True})["matches"]
    target = first_match(edit_matches) or first_match(document_matches)
    if not target:
        raise RuntimeError("No Edit or Document element found in active Notepad window.")

    print(f"Typing into {target['id']} ({target['control_type']})...")
    print(
        json.dumps(
            post(
                "/type",
                {
                    "element_id": target["id"],
                    "text": "Hello from UI Automation",
                    "clear_first": True,
                },
            ),
            indent=2,
        )
    )

    print("Sending ctrl+s...")
    print(json.dumps(post("/hotkey", {"keys": ["ctrl", "s"]}), indent=2))
    time.sleep(1.0)

    print("Observation after save hotkey:")
    print(json.dumps(get("/observe"), indent=2))


if __name__ == "__main__":
    main()
