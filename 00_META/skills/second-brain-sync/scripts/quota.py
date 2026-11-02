from dataclasses import dataclass
import json

@dataclass
class Quota:
    harness: str
    used_5h: float
    used_7d: float
    resets_at: int | str | None
    free_pct: float

def parse(ndjson: str, harness: str) -> Quota:
    try:
        data = json.loads(ndjson.strip())
    except (json.JSONDecodeError, AttributeError):
        raise ValueError("Invalid JSON")

    used_5h = 100.0
    used_7d = 100.0
    resets_at = None

    if harness in ("claude", "claude-code"):
        five_hour = data.get("fiveHour", {}) if isinstance(data, dict) else {}
        seven_day = data.get("sevenDay", {}) if isinstance(data, dict) else {}
        if isinstance(five_hour, dict) and five_hour.get("usedPercent") is not None:
            used_5h = float(five_hour["usedPercent"])
            resets_at = five_hour.get("resetsAt")
        if isinstance(seven_day, dict) and seven_day.get("usedPercent") is not None:
            used_7d = float(seven_day["usedPercent"])
    elif harness == "antigravity":
        groups = data.get("groups", []) if isinstance(data, dict) else []
        for g in groups:
            for w in g.get("windows", []):
                kind = w.get("windowKind")
                bucket = w.get("bucketId")
                if (kind == "5h" or bucket == "gemini-5h") and w.get("usedPercent") is not None:
                    used_5h = float(w["usedPercent"])
                    resets_at = w.get("resetsAt")
                elif (kind in ("weekly", "7d") or bucket == "gemini-weekly") and w.get("usedPercent") is not None:
                    used_7d = float(w["usedPercent"])

    free_pct = max(0.0, 100.0 - max(used_5h, used_7d))
    return Quota(harness=harness, used_5h=used_5h, used_7d=used_7d, resets_at=resets_at, free_pct=free_pct)
