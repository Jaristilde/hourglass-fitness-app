# Copyright © 2024-2025 [YOUR NAME]. All Rights Reserved.
#
# PROPRIETARY AND CONFIDENTIAL
#
# This file is part of Hourglass Fitness Transformation application.
# Unauthorized copying, distribution, or modification of this file,
# via any medium, is strictly prohibited.
#
# Contact: [your-email@example.com]
# storage.py
from __future__ import annotations
import json
from typing import Dict, Optional

import pandas as pd
from sqlalchemy import (
    Column, Integer, Float, String, create_engine, MetaData, Table,
    select, and_, insert, update, delete
)
from sqlalchemy.engine import Engine

_DB_PATH = "data.db"
engine: Optional[Engine] = None
metadata = MetaData()

# ---- Tables ----
profiles = Table(
    "profiles", metadata,
    Column("user_id", String, primary_key=True),
    Column("age", Integer, nullable=False),
    Column("sex", String, nullable=False),
    Column("height_cm", Float, nullable=False),
    Column("start_weight_kg", Float, nullable=False),
    Column("activity_level", String, nullable=False),
    Column("weekly_pace_lb", Float, nullable=False),
    Column("goal_weight_kg", Float, nullable=False),
    Column("goal_date", String, nullable=False),  # ISO date string
)

daily_logs = Table(
    "daily_logs", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", String, nullable=False, index=True),
    Column("date", String, nullable=False, index=True),  # ISO date string
    Column("weight_kg", Float, nullable=False),
    Column("water_l", Float, nullable=False),
    Column("cal_in", Integer, nullable=False),
    Column("cal_out", Integer, nullable=False),
    Column("net_kcal", Integer, nullable=False),
    Column("waist_in", Float, nullable=True),
    Column("hips_in", Float, nullable=True),
    Column("energy_1_10", Integer, nullable=True),
    Column("notes", String, nullable=True),
    Column("photo_path", String, nullable=True),
    Column("on_target_flag", String, nullable=True),
)

settings = Table(
    "settings", metadata,
    Column("user_id", String, primary_key=True),
    Column("macro_split_json", String, nullable=False),
)

# ---- Init ----
def init_storage():
    global engine
    if engine is None:
        engine = create_engine(f"sqlite:///{_DB_PATH}", future=True)
        metadata.create_all(engine)

# ---- Profiles ----
def save_profile(**kwargs):
    with engine.begin() as conn:
        exists = conn.execute(
            select(profiles.c.user_id).where(profiles.c.user_id == kwargs["user_id"])
        ).first()
        if exists:
            conn.execute(update(profiles).where(profiles.c.user_id == kwargs["user_id"]).values(**kwargs))
        else:
            conn.execute(insert(profiles).values(**kwargs))

def get_profile(user_id: str) -> Optional[Dict]:
    with engine.begin() as conn:
        row = conn.execute(
            select(profiles).where(profiles.c.user_id == user_id)
        ).mappings().first()
        return dict(row) if row else None

# ---- Settings ----
def save_settings(user_id: str, settings_dict: Dict):
    payload = json.dumps(settings_dict)
    with engine.begin() as conn:
        exists = conn.execute(
            select(settings.c.user_id).where(settings.c.user_id == user_id)
        ).first()
        if exists:
            conn.execute(update(settings).where(settings.c.user_id == user_id).values(macro_split_json=payload))
        else:
            conn.execute(insert(settings).values(user_id=user_id, macro_split_json=payload))

def get_settings(user_id: str) -> Optional[Dict]:
    with engine.begin() as conn:
        row = conn.execute(
            select(settings.c.macro_split_json).where(settings.c.user_id == user_id)
        ).first()
    return json.loads(row[0]) if row else None

# ---- Daily logs ----
def save_daily_log(
    user_id: str, date: str, weight_kg: float, water_l: float, cal_in: int, cal_out: int,
    waist_in: float, hips_in: float, energy_1_10: int, notes: str, photo_path: str, on_target_flag: str
):
    net = int(cal_in - cal_out)
    payload = dict(
        user_id=user_id, date=date, weight_kg=weight_kg, water_l=water_l,
        cal_in=cal_in, cal_out=cal_out, net_kcal=net,
        waist_in=waist_in, hips_in=hips_in, energy_1_10=energy_1_10,
        notes=notes, photo_path=photo_path, on_target_flag=on_target_flag,
    )
    with engine.begin() as conn:
        existing = conn.execute(
            select(daily_logs.c.id).where(and_(daily_logs.c.user_id == user_id, daily_logs.c.date == date))
        ).first()
        if existing:
            conn.execute(update(daily_logs).where(daily_logs.c.id == existing[0]).values(**payload))
        else:
            conn.execute(insert(daily_logs).values(**payload))

def get_logs(user_id: str, start: str, end: str) -> pd.DataFrame:
    with engine.begin() as conn:
        rows = conn.execute(
            select(daily_logs).where(
                and_(daily_logs.c.user_id == user_id, daily_logs.c.date >= start, daily_logs.c.date <= end)
            )
        ).mappings().all()
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame([dict(r) for r in rows])
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values("date")

# ---- Admin ----
def delete_all_user_data(user_id: str):
    with engine.begin() as conn:
        conn.execute(delete(daily_logs).where(daily_logs.c.user_id == user_id))
        conn.execute(delete(profiles).where(profiles.c.user_id == user_id))
        conn.execute(delete(settings).where(settings.c.user_id == user_id))

def export_logs_csv(user_id: str) -> str:
    df = get_logs(user_id, "1900-01-01", "2999-12-31")
    path = f"{user_id}_logs.csv"
    df.to_csv(path, index=False)
    return path
