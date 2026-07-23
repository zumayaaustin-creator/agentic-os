import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "agentic_os.db"


def _ensure_parent():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def _conn() -> sqlite3.Connection:
    _ensure_parent()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    _ensure_parent()
    conn = _conn()
    try:
        conn.executescript("""
CREATE TABLE IF NOT EXISTS kanban_tasks (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    body TEXT DEFAULT '',
    status TEXT DEFAULT 'triage',
    priority TEXT DEFAULT 'medium',
    assignee TEXT DEFAULT '',
    comments TEXT DEFAULT '[]',
    links TEXT DEFAULT '[]',
    created TEXT NOT NULL,
    updated TEXT NOT NULL,
    completed_at TEXT,
    summary TEXT,
    block_reason TEXT
);
CREATE TABLE IF NOT EXISTS goals (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT DEFAULT '',
    category TEXT DEFAULT 'general',
    target_date TEXT DEFAULT '',
    status TEXT DEFAULT 'active',
    progress INTEGER DEFAULT 0,
    created TEXT NOT NULL,
    updated TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS chat_messages (
    id TEXT PRIMARY KEY,
    role TEXT NOT NULL,
    agent TEXT NOT NULL,
    content TEXT NOT NULL,
    timestamp TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS cost_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    agent TEXT DEFAULT 'unknown',
    tokens INTEGER DEFAULT 0,
    cost REAL DEFAULT 0.0,
    model TEXT DEFAULT 'unknown'
);
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS audit_log (
    id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    action TEXT NOT NULL,
    details TEXT DEFAULT '{}'
);
CREATE TABLE IF NOT EXISTS plugins (
    name TEXT PRIMARY KEY,
    installed TEXT NOT NULL,
    version TEXT DEFAULT '1.0.0'
);
CREATE TABLE IF NOT EXISTS scheduler_jobs (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    skill TEXT NOT NULL,
    cron TEXT NOT NULL,
    enabled INTEGER DEFAULT 1,
    created TEXT NOT NULL,
    last_run TEXT,
    next_run TEXT
);
CREATE INDEX IF NOT EXISTS idx_chat_messages_ts ON chat_messages(timestamp);
CREATE INDEX IF NOT EXISTS idx_cost_entries_ts ON cost_entries(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_log_ts ON audit_log(timestamp);
""")
        conn.commit()
    finally:
        conn.close()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# Kanban

def db_get_kanban_tasks(status: Optional[str] = None) -> list[dict[str, Any]]:
    conn = _conn()
    try:
        if status:
            rows = conn.execute("SELECT * FROM kanban_tasks WHERE status = ?", (status,)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM kanban_tasks").fetchall()
        return [_row_to_task(r) for r in rows]
    finally:
        conn.close()


def db_get_kanban_task(task_id: str) -> Optional[dict[str, Any]]:
    conn = _conn()
    try:
        row = conn.execute("SELECT * FROM kanban_tasks WHERE id = ?", (task_id,)).fetchone()
        return _row_to_task(row) if row else None
    finally:
        conn.close()


def db_upsert_kanban_task(task: dict[str, Any]):
    conn = _conn()
    try:
        conn.execute("""
INSERT OR REPLACE INTO kanban_tasks (id, title, body, status, priority, assignee, comments, links, created, updated, completed_at, summary, block_reason)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", (
            task.get("id"),
            task.get("title"),
            task.get("body", ""),
            task.get("status", "triage"),
            task.get("priority", "medium"),
            task.get("assignee", ""),
            json.dumps(task.get("comments", [])),
            json.dumps(task.get("links", [])),
            task.get("created"),
            task.get("updated"),
            task.get("completed_at"),
            task.get("summary"),
            task.get("block_reason"),
        ))
        conn.commit()
    finally:
        conn.close()


def db_delete_kanban_task(task_id: str):
    conn = _conn()
    try:
        conn.execute("DELETE FROM kanban_tasks WHERE id = ?", (task_id,))
        conn.commit()
    finally:
        conn.close()


def _row_to_task(row: sqlite3.Row) -> dict[str, Any]:
    task = dict(row)
    task["comments"] = json.loads(task.get("comments") or "[]")
    task["links"] = json.loads(task.get("links") or "[]")
    return task


# Goals

def db_get_goals() -> list[dict[str, Any]]:
    conn = _conn()
    try:
        rows = conn.execute("SELECT * FROM goals").fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def db_upsert_goal(goal: dict[str, Any]):
    conn = _conn()
    try:
        conn.execute("""
INSERT OR REPLACE INTO goals (id, title, description, category, target_date, status, progress, created, updated)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
""", (
            goal.get("id"),
            goal.get("title"),
            goal.get("description", ""),
            goal.get("category", "general"),
            goal.get("target_date", ""),
            goal.get("status", "active"),
            goal.get("progress", 0),
            goal.get("created"),
            goal.get("updated"),
        ))
        conn.commit()
    finally:
        conn.close()


def db_delete_goal(goal_id: str):
    conn = _conn()
    try:
        conn.execute("DELETE FROM goals WHERE id = ?", (goal_id,))
        conn.commit()
    finally:
        conn.close()


# Chat

def db_get_chat_messages(limit: int = 200) -> list[dict[str, Any]]:
    conn = _conn()
    try:
        rows = conn.execute("SELECT * FROM chat_messages ORDER BY timestamp DESC LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in reversed(rows)]
    finally:
        conn.close()


def db_insert_chat_message(msg: dict[str, Any]):
    conn = _conn()
    try:
        conn.execute("""
INSERT INTO chat_messages (id, role, agent, content, timestamp) VALUES (?, ?, ?, ?, ?)
""", (
            msg.get("id"),
            msg.get("role"),
            msg.get("agent"),
            msg.get("content"),
            msg.get("timestamp"),
        ))
        conn.commit()
    finally:
        conn.close()


# Cost

def db_get_cost_entries() -> list[dict[str, Any]]:
    conn = _conn()
    try:
        rows = conn.execute("SELECT timestamp, agent, tokens, cost, model FROM cost_entries ORDER BY timestamp ASC").fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def db_insert_cost_entry(entry: dict[str, Any]):
    conn = _conn()
    try:
        conn.execute("""
INSERT INTO cost_entries (timestamp, agent, tokens, cost, model) VALUES (?, ?, ?, ?, ?)
""", (
            entry.get("timestamp"),
            entry.get("agent", "unknown"),
            entry.get("tokens", 0),
            entry.get("cost", 0.0),
            entry.get("model", "unknown"),
        ))
        conn.commit()
    finally:
        conn.close()


# Settings

def db_get_settings() -> dict[str, Any]:
    conn = _conn()
    try:
        rows = conn.execute("SELECT key, value FROM settings").fetchall()
        result = {}
        for r in rows:
            raw = r["value"]
            try:
                result[r["key"]] = json.loads(raw)
            except (json.JSONDecodeError, TypeError):
                result[r["key"]] = raw
        return result
    finally:
        conn.close()


def db_set_setting(key: str, value: Any):
    conn = _conn()
    try:
        conn.execute("""
INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)
""", (key, json.dumps(value) if not isinstance(value, str) else value))
        conn.commit()
    finally:
        conn.close()


# Audit

def db_insert_audit(entry: dict[str, Any]):
    conn = _conn()
    try:
        conn.execute("""
INSERT INTO audit_log (id, timestamp, action, details) VALUES (?, ?, ?, ?)
""", (
            entry.get("id"),
            entry.get("timestamp"),
            entry.get("action"),
            json.dumps({k: v for k, v in entry.items() if k not in ("id", "timestamp", "action")}),
        ))
        conn.commit()
    finally:
        conn.close()


def db_get_audit(limit: int = 100) -> list[dict[str, Any]]:
    conn = _conn()
    try:
        rows = conn.execute("SELECT id, timestamp, action, details FROM audit_log ORDER BY timestamp DESC LIMIT ?", (limit,)).fetchall()
        result = []
        for r in rows:
            item = {"id": r["id"], "timestamp": r["timestamp"], "action": r["action"]}
            try:
                item.update(json.loads(r["details"] or "{}"))
            except (json.JSONDecodeError, TypeError):
                pass
            result.append(item)
        return list(reversed(result))
    finally:
        conn.close()


# Plugins

def db_get_plugins() -> list[dict[str, Any]]:
    conn = _conn()
    try:
        rows = conn.execute("SELECT name, installed, version FROM plugins").fetchall()
        return [{"name": r["name"], "installed": r["installed"], "version": r["version"]} for r in rows]
    finally:
        conn.close()


def db_upsert_plugin(plugin: dict[str, Any]):
    conn = _conn()
    try:
        conn.execute("""
INSERT OR REPLACE INTO plugins (name, installed, version) VALUES (?, ?, ?)
""", (
            plugin.get("name"),
            plugin.get("installed"),
            plugin.get("version", "1.0.0"),
        ))
        conn.commit()
    finally:
        conn.close()


# Scheduler

def db_get_scheduler_jobs() -> list[dict[str, Any]]:
    conn = _conn()
    try:
        rows = conn.execute("SELECT * FROM scheduler_jobs").fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def db_upsert_scheduler_job(job: dict[str, Any]):
    conn = _conn()
    try:
        conn.execute("""
INSERT OR REPLACE INTO scheduler_jobs (id, name, skill, cron, enabled, created, last_run, next_run)
VALUES (?, ?, ?, ?, ?, ?, ?, ?)
""", (
            job.get("id"),
            job.get("name"),
            job.get("skill"),
            job.get("cron"),
            1 if job.get("enabled") else 0,
            job.get("created"),
            job.get("last_run"),
            job.get("next_run"),
        ))
        conn.commit()
    finally:
        conn.close()


def db_delete_scheduler_job(job_id: str):
    conn = _conn()
    try:
        conn.execute("DELETE FROM scheduler_jobs WHERE id = ?", (job_id,))
        conn.commit()
    finally:
        conn.close()
