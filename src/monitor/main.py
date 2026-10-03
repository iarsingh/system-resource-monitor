from fastapi import FastAPI
from monitor.check import check

app = FastAPI()

@app.post("/check")
def post_check(body: dict):
    return check(body)
