# -*- coding: utf-8 -*-
"""SQLite persistence for the company layer. It shares the discovery database file."""

from __future__ import annotations

import json
import time
from typing import Any, Dict, List, Optional

from agent_reach.discovery.storage import DiscoveryStorage
from agent_reach.team.models import Directive, Playbook, RoleSpec, Task

CUSTOM_ROLES_KEY = "team_custom_roles"
CUSTOM_PLAYBOOKS_KEY = "team_custom_playbooks"


class TeamStore:
    def __init__(self, storage: DiscoveryStorage):
        self.storage = storage
        self._init()

    def _init(self) -> None:
        with self.storage._connection() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS team_directives (
                    id TEXT PRIMARY KEY,
                    status TEXT,
                    data JSON,
                    created_at REAL,
                    updated_at REAL
                );
                CREATE TABLE IF NOT EXISTS team_tasks (
                    id TEXT PRIMARY KEY,
                    directive_id TEXT,
                    status TEXT,
                    data JSON,
                    created_at REAL,
                    updated_at REAL
                );
                CREATE TABLE IF NOT EXISTS team_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    directive_id TEXT,
                    task_id TEXT,
                    kind TEXT,
                    message TEXT,
                    created_at REAL
                );
                CREATE TABLE IF NOT EXISTS team_memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    kind TEXT,
                    text TEXT UNIQUE,
                    source TEXT,
                    uses INTEGER DEFAULT 0,
                    created_at REAL
                );
                CREATE INDEX IF NOT EXISTS idx_team_tasks_directive ON team_tasks (directive_id);
                CREATE INDEX IF NOT EXISTS idx_team_events_directive ON team_events (directive_id);
                """
            )

    # ── Directives ──

    def save_directive(self, d: Directive) -> Directive:
        d.updated_at = time.time()
        with self.storage._connection() as conn:
            conn.execute(
                """
                INSERT INTO team_directives (id, status, data, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET status=excluded.status, data=excluded.data, updated_at=excluded.updated_at
                """,
                (d.id, d.status, d.model_dump_json(), d.created_at, d.updated_at),
            )
        return d

    def get_directive(self, directive_id: str) -> Optional[Directive]:
        with self.storage._connection() as conn:
            row = conn.execute("SELECT data FROM team_directives WHERE id = ?", (directive_id,)).fetchone()
        return Directive.model_validate_json(row["data"]) if row else None

    def list_directives(self, limit: int = 20) -> List[Directive]:
        with self.storage._connection() as conn:
            rows = conn.execute(
                "SELECT data FROM team_directives ORDER BY created_at DESC LIMIT ?", (max(1, limit),)
            ).fetchall()
        return [Directive.model_validate_json(r["data"]) for r in rows]

    # ── Tasks ──

    def save_task(self, t: Task) -> Task:
        t.updated_at = time.time()
        with self.storage._connection() as conn:
            conn.execute(
                """
                INSERT INTO team_tasks (id, directive_id, status, data, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET status=excluded.status, data=excluded.data, updated_at=excluded.updated_at
                """,
                (t.id, t.directive_id, t.status, t.model_dump_json(), t.created_at, t.updated_at),
            )
        return t

    def get_task(self, task_id: str) -> Optional[Task]:
        with self.storage._connection() as conn:
            row = conn.execute("SELECT data FROM team_tasks WHERE id = ?", (task_id,)).fetchone()
        return Task.model_validate_json(row["data"]) if row else None

    def list_tasks(self, directive_id: str) -> List[Task]:
        with self.storage._connection() as conn:
            rows = conn.execute(
                "SELECT data FROM team_tasks WHERE directive_id = ? ORDER BY created_at, rowid", (directive_id,)
            ).fetchall()
        return [Task.model_validate_json(r["data"]) for r in rows]

    # ── Events ──

    def log(self, directive_id: str, kind: str, message: str, task_id: str = "") -> None:
        with self.storage._connection() as conn:
            conn.execute(
                "INSERT INTO team_events (directive_id, task_id, kind, message, created_at) VALUES (?, ?, ?, ?, ?)",
                (directive_id, task_id, kind, message[:600], time.time()),
            )

    def events(self, directive_id: str, limit: int = 60) -> List[Dict[str, Any]]:
        with self.storage._connection() as conn:
            rows = conn.execute(
                "SELECT task_id, kind, message, created_at FROM team_events WHERE directive_id = ? "
                "ORDER BY id DESC LIMIT ?",
                (directive_id, max(1, limit)),
            ).fetchall()
        return [dict(r) for r in reversed(rows)]

    # ── Company memory ──
    # Memory holds the owner's preferences and what the team learned. It guides planning.
    # It is never evidence: a claim cannot cite it.

    MEMORY_LIMIT = 200

    def remember(self, kind: str, text: str, source: str = "") -> bool:
        text = " ".join((text or "").split())[:400]
        if not text:
            return False
        with self.storage._connection() as conn:
            cur = conn.execute(
                "INSERT OR IGNORE INTO team_memory (kind, text, source, created_at) VALUES (?, ?, ?, ?)",
                (kind, text, source[:80], time.time()),
            )
            added = cur.rowcount > 0
            # Keep the newest rows. Owner preferences are never trimmed.
            conn.execute(
                "DELETE FROM team_memory WHERE kind != 'owner_preference' AND id NOT IN "
                "(SELECT id FROM team_memory WHERE kind != 'owner_preference' ORDER BY id DESC LIMIT ?)",
                (self.MEMORY_LIMIT,),
            )
        return added

    def memories(self, kinds: Optional[List[str]] = None, limit: int = 100) -> List[Dict[str, Any]]:
        with self.storage._connection() as conn:
            rows = conn.execute(
                "SELECT id, kind, text, source, uses, created_at FROM team_memory ORDER BY id DESC LIMIT ?",
                (max(1, limit),),
            ).fetchall()
        out = [dict(r) for r in rows]
        return [m for m in out if not kinds or m["kind"] in kinds]

    def forget(self, memory_id: int) -> bool:
        with self.storage._connection() as conn:
            cur = conn.execute("DELETE FROM team_memory WHERE id = ?", (int(memory_id),))
        return cur.rowcount > 0

    def touch_memories(self, ids: List[int]) -> None:
        if not ids:
            return
        with self.storage._connection() as conn:
            conn.executemany("UPDATE team_memory SET uses = uses + 1 WHERE id = ?", [(int(i),) for i in ids])

    def stale_running(self, before: float) -> List[Task]:
        """Tasks that have been running since before the given time."""
        with self.storage._connection() as conn:
            rows = conn.execute("SELECT data FROM team_tasks WHERE status = 'running'").fetchall()
        out = [Task.model_validate_json(r["data"]) for r in rows]
        return [t for t in out if (t.started_at or t.updated_at) < before]

    # ── Custom roles and playbooks (stored as settings) ──

    def custom_roles(self) -> Dict[str, RoleSpec]:
        raw = self.storage.get_setting(CUSTOM_ROLES_KEY, {}) or {}
        out: Dict[str, RoleSpec] = {}
        for name, data in raw.items():
            try:
                out[name] = RoleSpec.model_validate(data)
            except Exception:
                continue
        return out

    def save_custom_role(self, role: RoleSpec) -> None:
        raw = self.storage.get_setting(CUSTOM_ROLES_KEY, {}) or {}
        raw[role.name] = role.model_dump()
        self.storage.set_setting(CUSTOM_ROLES_KEY, raw)

    def custom_playbooks(self) -> Dict[str, Playbook]:
        raw = self.storage.get_setting(CUSTOM_PLAYBOOKS_KEY, {}) or {}
        out: Dict[str, Playbook] = {}
        for name, data in raw.items():
            try:
                out[name] = Playbook.model_validate(data)
            except Exception:
                continue
        return out

    def save_custom_playbook(self, pb: Playbook) -> None:
        raw = self.storage.get_setting(CUSTOM_PLAYBOOKS_KEY, {}) or {}
        raw[pb.name] = json.loads(pb.model_dump_json())
        self.storage.set_setting(CUSTOM_PLAYBOOKS_KEY, raw)
