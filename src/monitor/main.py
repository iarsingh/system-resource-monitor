from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from monitor.check import ReadingError, check, sustained

app = FastAPI()


class Series(BaseModel):
    samples: list[dict] = Field(min_length=1, max_length=1440)
    window: int = Field(default=3, ge=1, le=60)
    thresholds: dict[str, float] | None = None


def guarded(action):
    try:
        return action()
    except ReadingError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.post("/check")
def post_check(body: dict):
    thresholds = body.pop("thresholds", None)
    return guarded(lambda: check(body, thresholds))


@app.post("/check/series")
def post_series(body: Series):
    return guarded(lambda: sustained(body.samples, body.thresholds, body.window))
