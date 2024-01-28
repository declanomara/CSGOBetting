# An API to serve match data from the database using FastAPI

from fastapi import FastAPI

from src.database import Database

app = FastAPI()

DB_PATH = "matches.db"
db = Database(DB_PATH, auto_connect=False, auto_init=False)

@app.on_event("startup")
async def startup_event():
    db.connect()
    db.init()

@app.on_event("shutdown")
async def shutdown_event():
    db.close()

@app.get("/")
async def read_root():
    return {"Hello": "World"}

@app.get("/matches")
async def read_matches(limit: int = 100, before: int | None = None, after: int | None = None, status: int | None = None):
    # TODO: Add support for querying by team or teams

    if before is not None and after is not None:
        return [match.to_JSON() for match in db.get_matches_between_times(after, before)][0:limit]
    elif before is not None:
        return [match.to_JSON() for match in db.get_matches_before_time(before)][0:limit]
    elif after is not None:
        return [match.to_JSON() for match in db.get_matches_after_time(after)][0:limit]
    elif status is not None:
        return [match.to_JSON() for match in db.get_matches_by_status(status)][0:limit]
    else:
        return [match.to_JSON() for match in db.get_matches()][0:limit]

