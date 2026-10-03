def check(snapshot):
    alerts = [key for key in ("cpu_percent", "memory_percent", "disk_percent") if snapshot[key] >= 90]
    return {"alerts": alerts, "healthy": not alerts, "paged": False}
