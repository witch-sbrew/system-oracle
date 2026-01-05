from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import List
import time
import sqlite3
from datetime import datetime

app = FastAPI()
DB_PATH = "telemetry_history.db"


# python ver of struct ProcessInfo: { "pid": ..., "name": ..., "path": ... }
class ProcessInfo(BaseModel):
    pid: int
    name: str
    path: str
    start_time: int


# { "processes": [...] } structure
class ProcessList(BaseModel):
    processes: List[ProcessInfo]


# long-term mem (sqlite db)
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # We use 'uid' as the PRIMARY KEY so the 'ON CONFLICT' logic works
    c.execute(
        """CREATE TABLE IF NOT EXISTS activity (
            uid TEXT PRIMARY KEY, 
            pid INTEGER, 
            name TEXT, 
            path TEXT, 
            start_time INTEGER, 
            last_seen INTEGER, 
            status TEXT
        )"""
    )
    conn.commit()
    conn.close()


init_db()


@app.post("/telemetry/ingest")
async def ingest_telemetry(data: ProcessList):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    current_ts = int(time.time())

    # 0. THE JANITOR (Closes any processes not seen in 15 sec regardless of agent return)
    timeout_threshold = current_ts - 15
    c.execute(
        "UPDATE activity SET status = 'ENDED' WHERE status = 'ACTIVE' AND last_seen < ?",
        (timeout_threshold,),
    )

    # 1. THE UPSERT (Handling "New" and "Still Running")
    active_uids = []
    for p in data.processes:
        uid = f"{p.pid}_{p.start_time}"
        active_uids.append(uid)

        c.execute(
            """
            INSERT INTO activity (uid, pid, name, path, start_time, last_seen, status)
            VALUES (?, ?, ?, ?, ?, ?, 'ACTIVE')
            ON CONFLICT(uid) DO UPDATE SET 
                last_seen = excluded.last_seen,
                status = 'ACTIVE'
        """,
            (uid, p.pid, p.name, p.path, p.start_time, current_ts),
        )

    # 2. THE DEATH LOGIC (Mark missing processes as ENDED)
    # We use an empty list check to handle the SQL syntax correctly
    if len(active_uids) > 0:
        placeholders = ",".join(["?"] * len(active_uids))
        c.execute(
            f"UPDATE activity SET status = 'ENDED' WHERE status = 'ACTIVE' AND uid NOT IN ({placeholders})",
            active_uids,
        )
    else:
        # If the agent sent NO processes, everyone currently 'ACTIVE' must have ended
        c.execute("UPDATE activity SET status = 'ENDED' WHERE status = 'ACTIVE'")

    conn.commit()
    conn.close()
    return {"status": "ok"}


@app.get("/")
async def root():
    return {"message": "System Oracle Ground Station is Online"}


#### LEGACY CODE #####
# async def ingest_telemetry(data: ProcessList):
#     conn = sqlite3.connect(DB_PATH)
#     c = conn.cursor()
#     current_ts = int(time.time())

#     # 1. Track which UIDs are active in THIS snapshot
#     active_uids = []

#     for p in data.processes:
#         uid = f"{p.pid}_{p.start_time}"  # The Composite Key
#         active_uids.append(uid)

#         # 2. The UPSERT (Update or Insert)
#         # If UID exists, update last_seen. If not, create row.
#         c.execute(
#             """
#             INSERT INTO activity (uid, pid, name, path, start_time, last_seen, status)
#             VALUES (?, ?, ?, ?, ?, ?, 'ACTIVE')
#             ON CONFLICT(uid) DO UPDATE SET
#                 last_seen = excluded.last_seen,
#                 status = 'ACTIVE'
#         """,
#             (uid, p.pid, p.name, p.path, p.start_time, current_ts),
#         )

#     # 3. The "Death" Logic
#     # Find anyone marked ACTIVE who WASN'T in the list we just built
#     if data.processes:
#         placeholders = ",".join(["?"] * len(active_uids))
#         c.execute(
#             f"""
#             UPDATE activity
#             SET status = 'ENDED'
#             WHERE status = 'ACTIVE' AND uid NOT IN ({placeholders})
#         """,
#             active_uids,
#         )

#     conn.commit()
#     conn.close()
#     return {"status": "success"}


# async def ingest_telemetry(data: ProcessList):
#     now = datetime.now().isoformat()
#     conn = sqlite3.connect(DB_PATH)
#     c = conn.cursor()

#     # batch insert all processes found in this snapshot
#     log_data = [(now, p.pid, p.name, p.path, p.start_time) for p in data.processes]
#     c.executemany("INSERT INTO activity VALUES (?, ?, ?, ?)", log_data)

#     conn.commit()
#     conn.close()

#     print(
#         f"📥 [{datetime.now().strftime('%H:%M:%S')}] Saved {len(data.processes)} entries to database."
#     )
#     return {"status": "saved", "count": len(data.processes)}
# count = len(data.processes)
# timestamp = time.strftime("%H:%M:%S")

# print(f"📥 [{timestamp}] Received telemetry: {count} dev tools active.")
# if count > 0:
#     # Show a snippet of what we caught
#     names = [p.name for p in data.processes[:3]]
#     print(f"   Detected: {', '.join(names)}...")

# # trigger AI analysis somewhere

# return {"status": "success", "received": count}
