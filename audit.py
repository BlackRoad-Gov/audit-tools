#!/usr/bin/env python3
"""BlackRoad Audit Trail — immutable log of all governance actions"""
import sqlite3, hashlib, json, sys, os
from datetime import datetime, timezone

DB = os.path.expanduser("~/.blackroad/audit.db")

def init():
    os.makedirs(os.path.dirname(DB), exist_ok=True)
    db = sqlite3.connect(DB)
    db.executescript("""
    CREATE TABLE IF NOT EXISTS audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, actor TEXT,
        action TEXT, target TEXT, details TEXT, sha256 TEXT, parent_hash TEXT
    );""")
    return db

def log_action(actor, action, target, details=""):
    db = init()
    now = datetime.now(timezone.utc).isoformat()
    parent = db.execute("SELECT sha256 FROM audit_log ORDER BY id DESC LIMIT 1").fetchone()
    parent_hash = parent[0] if parent else "genesis"
    sha = hashlib.sha256(f"{now}|{actor}|{action}|{target}|{parent_hash}".encode()).hexdigest()
    db.execute("INSERT INTO audit_log VALUES (NULL,?,?,?,?,?,?,?)", (now, actor, action, target, details, sha, parent_hash))
    db.commit()
    print(f"Audit: {actor} {action} {target} [{sha[:12]}]")

def search(query):
    db = init()
    for ts, actor, action, target in db.execute(
        "SELECT timestamp,actor,action,target FROM audit_log WHERE actor LIKE ? OR action LIKE ? OR target LIKE ? ORDER BY id DESC LIMIT 20",
        (f"%{query}%",)*3):
        print(f"  [{ts[:19]}] {actor} → {action} → {target}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "log": log_action(*sys.argv[2:6])
    elif len(sys.argv) > 1 and sys.argv[1] == "search": search(sys.argv[2])
    else: print("Usage: audit.py [log <actor> <action> <target>|search <query>]")
