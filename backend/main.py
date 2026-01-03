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


# { "processes": [...] } structure
class ProcessList(BaseModel):
    processes: List[ProcessInfo]


# long-term mem (sqlite db)
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """CREATE TABLE IF NOT EXISTS activity
                 (timestamp TEXT, pid INTEGER, name TEXT, path TEXT)"""
    )
    conn.commit()
    conn.close()


init_db()


@app.post("/telemetry/ingest")
async def ingest_telemetry(data: ProcessList):
    now = datetime.now().isoformat()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # batch insert all processes found in this snapshot
    log_data = [(now, p.pid, p.name, p.path) for p in data.processes]
    c.executemany("INSERT INTO activity VALUES (?, ?, ?, ?)", log_data)

    conn.commit()
    conn.close()

    print(
        f"📥 [{datetime.now().strftime('%H:%M:%S')}] Saved {len(data.processes)} entries to database."
    )
    return {"status": "saved", "count": len(data.processes)}
    # count = len(data.processes)
    # timestamp = time.strftime("%H:%M:%S")

    # print(f"📥 [{timestamp}] Received telemetry: {count} dev tools active.")
    # if count > 0:
    #     # Show a snippet of what we caught
    #     names = [p.name for p in data.processes[:3]]
    #     print(f"   Detected: {', '.join(names)}...")

    # # trigger AI analysis somewhere

    # return {"status": "success", "received": count}


@app.get("/")
async def root():
    return {"message": "System Oracle Ground Station is Online"}
