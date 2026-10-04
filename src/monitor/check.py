RESOURCES = ("cpu_percent", "memory_percent", "disk_percent")
DEFAULT_THRESHOLDS = {"cpu_percent": 90, "memory_percent": 90, "disk_percent": 90}
RECOVER_GAP = 10


class ReadingError(ValueError):
    pass


def validate(snapshot):
    for key in RESOURCES:
        if key not in snapshot:
            raise ReadingError(f"{key} is missing")
        value = snapshot[key]
        if not isinstance(value, (int, float)) or isinstance(value, bool) or not 0 <= value <= 100:
            raise ReadingError(f"{key} must be a number from 0 to 100")


def check(snapshot, thresholds=None):
    validate(snapshot)
    limits = {**DEFAULT_THRESHOLDS, **(thresholds or {})}
    alerts = [key for key in RESOURCES if snapshot[key] >= limits[key]]
    return {"alerts": alerts, "healthy": not alerts, "paged": False}


def sustained(samples, thresholds=None, window=3):
    if window < 1:
        raise ReadingError("window must be at least 1")
    limits = {**DEFAULT_THRESHOLDS, **(thresholds or {})}
    for sample in samples:
        validate(sample)
    state = {key: {"firing": False, "streak": 0, "fired_at": None, "recovered_at": None} for key in RESOURCES}
    for index, sample in enumerate(samples):
        for key in RESOURCES:
            current = state[key]
            value = sample[key]
            if value >= limits[key]:
                current["streak"] += 1
                if not current["firing"] and current["streak"] >= window:
                    current["firing"] = True
                    current["fired_at"] = index
                    current["recovered_at"] = None
            else:
                current["streak"] = 0
                if current["firing"] and value < limits[key] - RECOVER_GAP:
                    current["firing"] = False
                    current["recovered_at"] = index
    firing = [key for key in RESOURCES if state[key]["firing"]]
    return {"firing": firing, "healthy": not firing, "window": window, "resources": state, "paged": False}
