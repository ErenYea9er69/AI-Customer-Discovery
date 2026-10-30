# -*- coding: utf-8 -*-
"""SQLite persistence layer for AI Customer Discovery & Lead Generation."""

from __future__ import annotations

import csv
import io
import json
import os
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional

from agent_reach.discovery.models import (
    BusinessProfile,
    Campaign,
    DiscoveredItem,
    GeneratedReply,
    LeadQualification,
    PostingSettings,
    ScoreBreakdown,
)

DEFAULT_DB_PATH = Path.home() / ".agent-reach" / "discovery.db"


class DiscoveryStorage:
    """Manages SQLite storage for profiles, campaigns, leads, replies, and logs."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextmanager
    def _connection(self) -> Generator[sqlite3.Connection, None, None]:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_db(self) -> None:
        with self._connection() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS business_profiles (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    url TEXT,
                    confirmed INTEGER DEFAULT 0,
                    data JSON,
                    created_at REAL,
                    updated_at REAL
                );

                CREATE TABLE IF NOT EXISTS campaigns (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    business_profile_id TEXT,
                    status TEXT,
                    data JSON,
                    created_at REAL,
                    completed_at REAL
                );

                CREATE TABLE IF NOT EXISTS discovered_items (
                    id TEXT PRIMARY KEY,
                    url TEXT UNIQUE,
                    platform TEXT,
                    community TEXT,
                    author TEXT,
                    title TEXT,
                    content TEXT,
                    data JSON,
                    created_at REAL
                );

                CREATE TABLE IF NOT EXISTS leads (
                    id TEXT PRIMARY KEY,
                    discovered_item_id TEXT,
                    campaign_id TEXT,
                    url TEXT,
                    platform TEXT,
                    community TEXT,
                    title TEXT,
                    customer_problem TEXT,
                    pain_point_category TEXT,
                    buying_intent TEXT,
                    urgency TEXT,
                    score INTEGER,
                    classification TEXT,
                    confidence REAL,
                    data JSON,
                    created_at REAL
                );

                CREATE TABLE IF NOT EXISTS replies (
                    id TEXT PRIMARY KEY,
                    lead_id TEXT UNIQUE,
                    status TEXT,
                    selected_version TEXT,
                    data JSON,
                    created_at REAL,
                    updated_at REAL
                );

                CREATE TABLE IF NOT EXISTS posting_logs (
                    id TEXT PRIMARY KEY,
                    lead_id TEXT,
                    reply_id TEXT,
                    platform TEXT,
                    target_url TEXT,
                    content TEXT,
                    mode TEXT,
                    status TEXT,
                    error_message TEXT,
                    created_at REAL
                );

                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value JSON,
                    updated_at REAL
                );

                CREATE INDEX IF NOT EXISTS idx_leads_score ON leads (score DESC);
                CREATE INDEX IF NOT EXISTS idx_leads_classification ON leads (classification);
                CREATE INDEX IF NOT EXISTS idx_discovered_url ON discovered_items (url);
                """
            )

    # ── Business Profiles ──

    def save_business_profile(self, profile: BusinessProfile) -> None:
        profile.updated_at = time.time()
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO business_profiles (id, name, url, confirmed, data, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name=excluded.name,
                    url=excluded.url,
                    confirmed=excluded.confirmed,
                    data=excluded.data,
                    updated_at=excluded.updated_at
                """,
                (
                    profile.id,
                    profile.name,
                    profile.url or "",
                    1 if profile.confirmed else 0,
                    profile.model_dump_json(),
                    profile.created_at,
                    profile.updated_at,
                ),
            )

    def get_business_profile(self, profile_id: str) -> Optional[BusinessProfile]:
        with self._connection() as conn:
            row = conn.execute("SELECT data FROM business_profiles WHERE id = ?", (profile_id,)).fetchone()
            if row:
                return BusinessProfile.model_validate_json(row["data"])
        return None

    def get_latest_business_profile(self) -> Optional[BusinessProfile]:
        with self._connection() as conn:
            row = conn.execute(
                "SELECT data FROM business_profiles ORDER BY updated_at DESC LIMIT 1"
            ).fetchone()
            if row:
                return BusinessProfile.model_validate_json(row["data"])
        return None

    # ── Campaigns ──

    def save_campaign(self, campaign: Campaign) -> None:
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO campaigns (id, name, business_profile_id, status, data, created_at, completed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name=excluded.name,
                    status=excluded.status,
                    data=excluded.data,
                    completed_at=excluded.completed_at
                """,
                (
                    campaign.id,
                    campaign.name,
                    campaign.business_profile_id,
                    campaign.status,
                    campaign.model_dump_json(),
                    campaign.created_at,
                    campaign.completed_at,
                ),
            )

    def get_campaign(self, campaign_id: str) -> Optional[Campaign]:
        with self._connection() as conn:
            row = conn.execute("SELECT data FROM campaigns WHERE id = ?", (campaign_id,)).fetchone()
            if row:
                return Campaign.model_validate_json(row["data"])
        return None

    def list_campaigns(self, limit: int = 50) -> List[Campaign]:
        with self._connection() as conn:
            rows = conn.execute("SELECT data FROM campaigns ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
            return [Campaign.model_validate_json(r["data"]) for r in rows]

    # ── Discovered Items & Deduplication ──

    def save_discovered_item(self, item: DiscoveredItem) -> bool:
        """Saves item. Returns True if inserted, False if duplicate."""
        try:
            with self._connection() as conn:
                conn.execute(
                    """
                    INSERT INTO discovered_items (id, url, platform, community, author, title, content, data, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        item.id,
                        item.url,
                        item.platform,
                        item.community,
                        item.author,
                        item.title,
                        item.content,
                        item.model_dump_json(),
                        item.created_at,
                    ),
                )
                return True
        except sqlite3.IntegrityError:
            return False

    def is_url_discovered(self, url: str) -> bool:
        with self._connection() as conn:
            row = conn.execute("SELECT 1 FROM discovered_items WHERE url = ?", (url,)).fetchone()
            return row is not None

    # ── Leads ──

    def save_lead(self, lead: LeadQualification, campaign_id: str = "") -> None:
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO leads (
                    id, discovered_item_id, campaign_id, url, platform, community,
                    title, customer_problem, pain_point_category, buying_intent, urgency,
                    score, classification, confidence, data, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    score=excluded.score,
                    classification=excluded.classification,
                    confidence=excluded.confidence,
                    data=excluded.data
                """,
                (
                    lead.id,
                    lead.discovered_item_id,
                    campaign_id,
                    lead.url,
                    lead.platform,
                    lead.community,
                    lead.title,
                    lead.customer_problem,
                    lead.pain_point_category,
                    lead.purchase_intent,
                    lead.urgency,
                    lead.score,
                    lead.classification,
                    lead.confidence,
                    lead.model_dump_json(),
                    lead.created_at,
                ),
            )

    def get_lead(self, lead_id: str) -> Optional[LeadQualification]:
        with self._connection() as conn:
            row = conn.execute("SELECT data FROM leads WHERE id = ?", (lead_id,)).fetchone()
            if row:
                return LeadQualification.model_validate_json(row["data"])
        return None

    def list_leads(
        self,
        min_score: int = 0,
        platform: Optional[str] = None,
        classification: Optional[str] = None,
        pain_point_category: Optional[str] = None,
        buying_intent: Optional[str] = None,
        query: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[LeadQualification]:
        conditions = ["score >= ?"]
        params: List[Any] = [min_score]

        if platform:
            conditions.append("platform = ?")
            params.append(platform)
        if classification:
            conditions.append("classification = ?")
            params.append(classification)
        if pain_point_category:
            conditions.append("pain_point_category = ?")
            params.append(pain_point_category)
        if buying_intent:
            conditions.append("buying_intent = ?")
            params.append(buying_intent)
        if query:
            conditions.append("(title LIKE ? OR customer_problem LIKE ?)")
            params.extend([f"%{query}%", f"%{query}%"])

        params.extend([limit, offset])
        sql = f"""
            SELECT data FROM leads
            WHERE {' AND '.join(conditions)}
            ORDER BY score DESC, created_at DESC
            LIMIT ? OFFSET ?
        """
        with self._connection() as conn:
            rows = conn.execute(sql, params).fetchall()
            return [LeadQualification.model_validate_json(r["data"]) for r in rows]

    def count_leads(self) -> Dict[str, int]:
        with self._connection() as conn:
            total = conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
            high_potential = conn.execute(
                "SELECT COUNT(*) FROM leads WHERE classification = 'high_potential'"
            ).fetchone()[0]
            relevant = conn.execute(
                "SELECT COUNT(*) FROM leads WHERE classification = 'relevant_potential'"
            ).fetchone()[0]
            insights = conn.execute(
                "SELECT COUNT(*) FROM leads WHERE classification = 'customer_insight'"
            ).fetchone()[0]
            competitors = conn.execute(
                "SELECT COUNT(*) FROM leads WHERE classification = 'competitor_intel'"
            ).fetchone()[0]
            return {
                "total": total,
                "high_potential": high_potential,
                "relevant": relevant,
                "customer_insights": insights,
                "competitor_intel": competitors,
            }

    # ── Replies ──

    def save_reply(self, reply: GeneratedReply) -> None:
        reply.updated_at = time.time()
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO replies (id, lead_id, status, selected_version, data, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    status=excluded.status,
                    selected_version=excluded.selected_version,
                    data=excluded.data,
                    updated_at=excluded.updated_at
                """,
                (
                    reply.id,
                    reply.lead_id,
                    reply.status,
                    reply.selected_version,
                    reply.model_dump_json(),
                    reply.created_at,
                    reply.updated_at,
                ),
            )

    def get_reply_by_lead_id(self, lead_id: str) -> Optional[GeneratedReply]:
        with self._connection() as conn:
            row = conn.execute("SELECT data FROM replies WHERE lead_id = ?", (lead_id,)).fetchone()
            if row:
                return GeneratedReply.model_validate_json(row["data"])
        return None

    def list_replies(self, status: Optional[str] = None, limit: int = 100) -> List[GeneratedReply]:
        with self._connection() as conn:
            if status:
                rows = conn.execute(
                    "SELECT data FROM replies WHERE status = ? ORDER BY updated_at DESC LIMIT ?",
                    (status, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT data FROM replies ORDER BY updated_at DESC LIMIT ?", (limit,)
                ).fetchall()
            return [GeneratedReply.model_validate_json(r["data"]) for r in rows]

    # ── Posting Logs ──

    def log_post(
        self,
        lead_id: str,
        reply_id: str,
        platform: str,
        target_url: str,
        content: str,
        mode: str,
        status: str,
        error_message: Optional[str] = None,
    ) -> None:
        import uuid

        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO posting_logs (
                    id, lead_id, reply_id, platform, target_url, content, mode, status, error_message, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(uuid.uuid4()),
                    lead_id,
                    reply_id,
                    platform,
                    target_url,
                    content,
                    mode,
                    status,
                    error_message or "",
                    time.time(),
                ),
            )

    def count_posts_today(self, platform: Optional[str] = None) -> int:
        start_of_day = time.time() - (time.time() % 86400)
        with self._connection() as conn:
            if platform:
                row = conn.execute(
                    """
                    SELECT COUNT(*) FROM posting_logs
                    WHERE platform = ? AND status = 'published' AND created_at >= ?
                    """,
                    (platform, start_of_day),
                ).fetchone()
            else:
                row = conn.execute(
                    """
                    SELECT COUNT(*) FROM posting_logs
                    WHERE status = 'published' AND created_at >= ?
                    """,
                    (start_of_day,),
                ).fetchone()
            return row[0] if row else 0

    # ── Settings ──

    def get_setting(self, key: str, default: Any = None) -> Any:
        with self._connection() as conn:
            row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
            if row:
                return json.loads(row["value"])
        return default

    def set_setting(self, key: str, value: Any) -> None:
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO settings (key, value, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at
                """,
                (key, json.dumps(value), time.time()),
            )

    # ── Exporting (CSV / JSON) ──

    def export_leads_json(self, min_score: int = 0) -> str:
        leads = self.list_leads(min_score=min_score, limit=1000)
        return json.dumps([l.model_dump() for l in leads], indent=2)

    def export_leads_csv(self, min_score: int = 0) -> str:
        leads = self.list_leads(min_score=min_score, limit=1000)
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "Lead ID",
            "Title",
            "Score",
            "Classification",
            "Platform",
            "Community",
            "Author",
            "Date",
            "URL",
            "Customer Problem",
            "Pain Point Category",
            "Buying Intent",
            "Urgency",
            "Evidence",
        ])
        for lead in leads:
            writer.writerow([
                lead.id,
                lead.title,
                lead.score,
                lead.classification,
                lead.platform,
                lead.community,
                lead.author,
                lead.published_at,
                lead.url,
                lead.customer_problem,
                lead.pain_point_category,
                lead.purchase_intent,
                lead.urgency,
                lead.evidence,
            ])
        return output.getvalue()
