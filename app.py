# Copyright © 2024-2025 [YOUR NAME]. All Rights Reserved.
#
# PROPRIETARY AND CONFIDENTIAL
#
# This file is part of Hourglass Fitness Transformation application.
# Unauthorized copying, distribution, or modification of this file,
# via any medium, is strictly prohibited.
#
# Contact: [your-email@example.com]
# streamlit_app.py
# Hourglass Workout Program by Joane Aristilde - Enhanced with Video Support

import streamlit as st
from textwrap import dedent
import re
from datetime import date, datetime, timedelta
import json
import os
from typing import Dict, Optional, List
import pandas as pd
import numpy as np


# SAFE FLAGS
def _get_bool(name: str, default=False) -> bool:
    val = os.environ.get(name)
    if val is None:
        try:
            val = st.secrets.get(name, "true" if default else "false")
        except Exception:
            val = "true" if default else "false"
    return str(val).strip().lower() in ("1", "true", "yes", "on")


ADMIN_MODE = _get_bool("ADMIN_MODE", False)
READ_ONLY = _get_bool("READ_ONLY", False)
ADMIN_UI = ADMIN_MODE and not READ_ONLY

# Import storage functions with error handling
try:
    from storage import (
        init_storage, get_profile, save_profile, get_settings, save_settings,
        save_daily_log, get_logs, delete_all_user_data, export_logs_csv,
    )

    STORAGE_AVAILABLE = True
except ImportError:
    STORAGE_AVAILABLE = False


    # Dummy functions if storage module is not available
    def init_storage():
        pass


    def get_profile(user_id):
        return None


    def save_profile(**kwargs):
        pass


    def get_settings(user_id):
        return None


    def save_settings(user_id, settings):
        pass


    def save_daily_log(**kwargs):
        pass


    def get_logs(user_id, start, end):
        return pd.DataFrame()


    def delete_all_user_data(user_id):
        pass


    def export_logs_csv(user_id):
        return "export.csv"

# ============================================================================
# CONFIGURATION & CONSTANTS
# ============================================================================
st.set_page_config(
    page_title="Hourglass Fitness Transformation",
    page_icon="💪",
    layout="wide",
    initial_sidebar_state="expanded"
)

MAX_VIDEO_MB = 50
UPLOAD_ROOT = "uploaded_content"
MAIN_MEDIA_DIR = os.path.join(UPLOAD_ROOT, "main_media")
EXERCISE_VIDEOS_DIR = os.path.join(UPLOAD_ROOT, "exercise_videos")
PROGRESS_DIR = os.path.join(UPLOAD_ROOT, "progress_photos")
USER_DATA_DIR = "user_data"
VIDEOS_DIR = "videos"
VIDEOS_JSON = "videos.json"
WORKOUT_LOG_CSV = "workout_log.csv"
USER_PROGRESS_JSON = os.path.join(USER_DATA_DIR, "user_progress.json")
VIDEOS_DB_JSON = os.path.join(EXERCISE_VIDEOS_DIR, "videos_db.json")

# Badge definitions
BADGES = [
    {"key": "first_week", "label": "✅ 7-Day Starter", "rule": lambda s: s.get("longest", 0) >= 7},
    {"key": "hydration_pro", "label": "💧 Hydration Pro", "rule": lambda s: s.get("hydration7", False)},
    {"key": "glute_grind", "label": "🍑 Glute Grind", "rule": lambda s: s.get("glute_sets_2wk", 0) >= 12},
    {"key": "consistency", "label": "🔥 21-Day Habit", "rule": lambda s: s.get("longest", 0) >= 21},
    {"key": "early_bird", "label": "🌅 Early Bird", "rule": lambda s: s.get("morning_workouts", 0) >= 5},
]

# ============================================================================
# WORKOUT DATA
# ============================================================================
PROGRAM_SPLIT = {
    "Level 1": {
        "Monday": "BOOTY",
        "Tuesday": "ABS/CORE & CARDIO",
        "Wednesday": "REST",
        "Thursday": "LEGS & BOOTY",
        "Friday": "ABS/CORE ONLY (you can do at home)",
        "Saturday": "LIGHT SHOULDERS & BACK",
        "Sunday": "REST"
    },
        "Level 2": {
        "Monday": "BOOTY A",
        "Tuesday": "LIGHT SHOULDERS & BACK",
        "Wednesday": "ABS/CORE & CARDIO",
        "Thursday": "BOOTY B",
        "Friday": "SHOULDERS & ABS/CORE",
        "Saturday": "LEGS & BOOTY",
        "Sunday": "REST"
    }
}


# Exercise definitions
def warmup_item():
    return {"name": "Booty/Leg Activation", "sets": "—", "reps": "5 min", "category": "Warm-up"}


def stretching_item():
    return {"name": "Stretching", "sets": "—", "reps": "5 min", "category": "Recovery"}


def stairmaster_L1():
    return {"name": "Stairmaster Workout", "sets": "—", "reps": "30 min: fat loss levels 8-10", "category": "Cardio"}


def stairmaster_L2():
    return {"name": "Stairmaster Workout", "sets": "—", "reps": "30 min: fat loss levels 8-10", "category": "Cardio"}


# Core exercises
KICKBACKS = {"name": "Kickbacks", "sets": "1 warm up set + 3 (each side)", "reps": "10-12 reps; 12-15 reps (last set)",
             "category": "Booty"}
HIP_THRUST = {"name": "Hip Thrust", "sets": "1 warm up set + 3 + 1 AMRAP",
              "reps": "10-12 reps; 8 reps (last set); AMRAP ~20% avg weight", "category": "Booty"}
HYPEREXT = {"name": "Hyperextensions", "sets": "(1 warm up set) + 3 + 1 AMRAP (no weight)",
            "reps": "10-12 reps; 10s hold on last rep each set", "category": "Booty"}
RDLS = {"name": "RDLs (Romanian Deadlifts)", "sets": "1 warm up set + 3", "reps": "10-12 reps; 8 reps (last set)",
        "category": "Booty"}

# Workout lists - simplified
BOOTY_L1 = [warmup_item(), KICKBACKS, HIP_THRUST, HYPEREXT, RDLS, stairmaster_L1(), stretching_item()]

ABS_CORE_ONLY = [
    {"name": "Plank", "sets": "1", "reps": "1 min", "category": "Core"},
    {"name": "Plank Knee Taps", "sets": "1", "reps": "30 sec", "category": "Core"},
    {"name": "Reverse Plank", "sets": "1", "reps": "1 min", "category": "Core"},
    {"name": "Butterfly Kicks", "sets": "1", "reps": "30 sec", "category": "Core"},
    {"name": "Half Leg Raises", "sets": "1", "reps": "30 sec", "category": "Core"},
    {"name": "Dead Bugs", "sets": "1", "reps": "30 sec", "category": "Core"},
    {"name": "Repeat 2x total", "sets": "—", "reps": "Complete entire circuit twice", "category": "Core"}
]

# ============================================================================
# MEAL PLAN DATA
# ============================================================================
WEEKLY_MEALS = {
    "Option A: Omnivore": {
        "Monday": ["Greek yogurt + berries + oats", "Chicken, rice & broccoli", "Salmon, sweet potato, asparagus"],
        "Tuesday": ["Omelet + toast + fruit", "Turkey wrap + mixed greens", "Beef stir-fry + jasmine rice"],
        "Wednesday": ["Protein smoothie + banana + PB", "Chicken fajita bowl", "Shrimp tacos + slaw"],
        "Thursday": ["Overnight oats + chia + berries", "Sushi bowl (salmon, rice, edamame)",
                     "Lean beef chili + quinoa"],
        "Friday": ["Eggs + avocado toast", "Grilled chicken Caesar", "Baked cod + potatoes + green beans"],
        "Saturday": ["Protein pancakes + fruit", "Turkey burger + salad", "Steak + rice + vegetables"],
        "Sunday": ["Cottage cheese + pineapple + granola", "Chicken pesto pasta + veggies",
                   "Roast chicken + couscous + salad"]
    },
    "Option B: Pescatarian": {
        "Monday": ["Greek yogurt + berries + oats", "Tuna salad wrap + greens", "Salmon, sweet potato, asparagus"],
        "Tuesday": ["Tofu scramble + toast", "Shrimp quinoa bowl", "Baked cod + potatoes + broccoli"],
        "Wednesday": ["Protein smoothie + banana", "Sushi bowl", "Garlic shrimp pasta + salad"],
        "Thursday": ["Overnight oats + chia", "Miso salmon + rice + bok choy", "Veggie chili + avocado toast"],
        "Friday": ["Eggs + avocado toast", "Mediterranean tuna pasta", "Seared tuna + rice + edamame"],
        "Saturday": ["Protein pancakes + fruit", "Grilled shrimp tacos + slaw", "Baked halibut + quinoa + veg"],
        "Sunday": ["Cottage cheese + fruit", "Smoked salmon bagel", "Shrimp stir-fry + brown rice"]
    },
    "Option C: Vegan": {
        "Monday": ["Tofu scramble + toast + fruit", "Lentil quinoa bowl + veggies", "Tempeh stir-fry + rice"],
        "Tuesday": ["Overnight oats + chia + berries", "Chickpea wrap + greens", "Black bean pasta + broccoli"],
        "Wednesday": ["Pea-protein smoothie + banana + PB", "Buddha bowl", "Lentil curry + basmati rice"],
        "Thursday": ["Buckwheat pancakes + fruit", "Hummus + falafel bowl", "Tofu poke bowl"],
        "Friday": ["Tofu scramble burrito", "Pea-protein pasta + marinara", "Tempeh fajitas + tortillas"],
        "Saturday": ["Oatmeal + seeds + berries", "Chickpea quinoa bowl", "Tofu steak + potatoes + veg"],
        "Sunday": ["Soy yogurt + granola + fruit", "Vegan sushi + edamame", "Lentil bolognese + pasta"]
    }
}

# Exercise alternatives
EXERCISE_ALTERNATIVES = {
    "bulgarian_split_squats": {
        "low_impact": ["Goblet Squats", "Wall Sits", "Leg Press"],
        "at_home": ["Static Lunges", "Step-ups", "Single-leg Glute Bridges"]
    },
    "hip_thrust": {
        "low_impact": ["Glute Bridges", "Clamshells", "Donkey Kicks"],
        "at_home": ["Single-leg Glute Bridges", "Frog Pumps", "Elevated Glute Bridges"]
    },
    "rdls_romanian_deadlifts": {
        "low_impact": ["Good Mornings", "Cable Pull-throughs", "Seated Hamstring Curls"],
        "at_home": ["Single-leg RDLs", "Nordic Curls", "Hamstring Walkouts"]
    }
}


# ============================================================================
# INITIALIZATION & HELPERS
# ============================================================================
def ensure_dirs():
    """Create necessary directories if they don't exist"""
    dirs = [
        UPLOAD_ROOT, MAIN_MEDIA_DIR, EXERCISE_VIDEOS_DIR,
        PROGRESS_DIR, USER_DATA_DIR, VIDEOS_DIR
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)


def init_session_state():
    """Initialize session state variables - FIXED to ensure all keys exist"""
    if 'initialized' not in st.session_state:
        st.session_state.initialized = True
        ensure_dirs()

    defaults = {
        'page': 'home',
        'completed_exercises': [],
        'selected_level': 1,
        'progress_entries': [],
        'selected_workout': None,
        'selected_workout_day': None,
        'weight_entries': [],
        'meal_plan_option': 'Option A: Omnivore',
        'workout_sets': {},
        'coach_history': [],  # MUST be initialized
        'display_name': '',
        'community_chat': [],
        'device_metrics': {},
        'a11y_scale': 1.0,
        'a11y_theme': 'auto',
        'a11y_reduced_motion': False,
        'language': 'en',
        'prefs': {
            "experience": "beginner",
            "focus": ["glutes", "core"],
            "equipment": ["dumbbells", "machines", "bodyweight"]
        },
        'ai_tuning': {
            "injury_notes": "",
            "available_days": 4,
            "diet": "omnivore",
            "protein_target_g": 120
        },
        'badges_earned': [],
        'reminder_prefs': {
            "enabled": False,
            "days": [],
            "time": "08:00"
        },
        'show_prefs_editor': False
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    # Load user progress data
    load_user_progress()


def load_styles():
    """Load custom CSS styles"""
    st.markdown("""
    <style>
        .main {
            background: linear-gradient(135deg, #ffeef8 0%, #fff5f8 50%, #f0f8ff 100%);
        }
        .main-header {
            font-size: 3rem;
            font-weight: 800;
            text-align: center;
            background: linear-gradient(45deg, #FF1493, #FF69B4, #DA70D6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
            margin-bottom: .5rem;
        }
        .sub-header {
            font-size: 1.1rem;
            text-align: center;
            color: #666;
            margin-bottom: 1rem;
            font-weight: 300;
        }
        .hero-section {
            text-align: center;
            padding: 2rem;
            background: linear-gradient(135deg, rgba(255,20,147,.15), rgba(255,105,180,.15), rgba(218,112,214,.15));
            border-radius: 18px;
            margin-bottom: 20px;
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px rgba(0,0,0,.08);
            border: 1px solid rgba(255,255,255,.35);
        }
        .nav-button {
            background: linear-gradient(135deg, #FF69B4, #DA70D6);
            color: white;
            padding: 1.5rem;
            border-radius: 15px;
            text-align: center;
            font-size: 1.2rem;
            font-weight: 600;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            transition: transform 0.2s;
            cursor: pointer;
        }
        .nav-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0,0,0,0.15);
        }
        .info-card {
            background: white;
            padding: 1.5rem;
            border-radius: 12px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 1rem;
        }
        .weekly-box {
            background: rgba(255,255,255,.96);
            padding: 12px;
            border-radius: 14px;
            margin: 8px 0 14px 0;
            box-shadow: 0 4px 15px rgba(0,0,0,.08);
            border-left: 5px solid #FF1493;
        }
        .category-header {
            background: linear-gradient(45deg,#FF69B4,#DA70D6);
            color:#fff;
            padding: 10px;
            border-radius: 10px;
            text-align:center;
            font-weight:700;
            margin: 12px 0 8px 0;
        }
        .exercise-card {
            background: rgba(255,255,255,.98);
            padding: 12px;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0,0,0,.08);
            margin: 8px 0;
            border-left: 5px solid #FF1493;
        }
        .completed-card {
            background: rgba(232,245,232,.95);
            border-left: 5px solid #4CAF50;
        }
        .badge {
            display:inline-block;
            padding:6px 10px;
            border-radius:12px;
            color:#fff;
            font-weight:700;
            margin:6px 0;
        }
    </style>
    """, unsafe_allow_html=True)


# ============================================================================
# NEW: USER PROGRESS PERSISTENCE
# ============================================================================
def load_user_progress():
    """Load user progress data from JSON"""
    try:
        if os.path.exists(USER_PROGRESS_JSON):
            with open(USER_PROGRESS_JSON, 'r') as f:
                data = json.load(f)
                # Merge with session state
                for key in ['prefs', 'ai_tuning', 'badges_earned', 'reminder_prefs']:
                    if key in data:
                        st.session_state[key] = data[key]
    except Exception as e:
        # Silently fail and use defaults
        pass


def save_user_progress():
    """Save user progress data to JSON"""
    try:
        data = {
            "prefs": st.session_state.get("prefs", {}),
            "ai_tuning": st.session_state.get("ai_tuning", {}),
            "badges_earned": st.session_state.get("badges_earned", []),
            "reminder_prefs": st.session_state.get("reminder_prefs", {}),
            "display_name": st.session_state.get("display_name", ""),
            "weight_entries": st.session_state.get("weight_entries", []),
            "progress_entries": st.session_state.get("progress_entries", []),
        }
        with open(USER_PROGRESS_JSON, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        # Silently fail
        pass


# ============================================================================
# NEW: PERSONALIZATION HELPERS
# ============================================================================
def generate_smart_suggestions():
    """Generate personalized suggestions based on user data"""
    suggestions = []

    # Analyze last 7 days of data - FIXED with safe access
    weight_entries = st.session_state.get("weight_entries", [])
    if weight_entries:
        recent_entries = weight_entries[-7:]
        avg_water = sum(e.get("water", 0) for e in recent_entries) / len(recent_entries)
        if avg_water < 2:
            suggestions.append("💧 Increase water intake to 2-3L daily for better recovery")

    # Based on experience level - FIXED with safe access
    prefs = st.session_state.get("prefs", {})
    exp = prefs.get("experience", "beginner")
    if exp == "beginner":
        suggestions.append("📚 Focus on form over weight - film yourself to check technique")
    elif exp == "intermediate":
        suggestions.append("🔥 Try adding drop sets to your last exercise for extra burn")

    # Based on focus areas
    focus = prefs.get("focus", [])
    if "glutes" in focus:
        suggestions.append("🍑 Add pause reps to hip thrusts (3 sec at top)")
    if "core" in focus:
        suggestions.append("💪 Try hollow body holds between sets for extra core work")

    # Based on available days - FIXED with safe access
    ai_tuning = st.session_state.get("ai_tuning", {})
    days = ai_tuning.get("available_days", 4)
    if days < 3:
        suggestions.append("⚡ Combine upper/lower on same day to maximize your 2 sessions")

    return suggestions[:5]  # Return top 5 suggestions


def render_personalization_card():
    """Render the personalization card with smart suggestions"""
    with st.expander("🎯 Smart Suggestions for You", expanded=True):
        col1, col2 = st.columns([2, 1])

        with col1:
            suggestions = generate_smart_suggestions()
            if suggestions:
                for suggestion in suggestions:
                    st.write(suggestion)
            else:
                st.info("Complete a few workouts to get personalized suggestions!")

        with col2:
            if st.button("⚙️ Update Preferences"):
                st.session_state.show_prefs_editor = True

        # Preferences editor - FIXED with safe access
        if st.session_state.get("show_prefs_editor", False):
            st.markdown("### Edit Your Preferences")

            # Ensure prefs and ai_tuning exist
            if "prefs" not in st.session_state:
                st.session_state.prefs = {}
            if "ai_tuning" not in st.session_state:
                st.session_state.ai_tuning = {}

            # Experience level
            st.session_state.prefs["experience"] = st.selectbox(
                "Experience Level",
                ["beginner", "intermediate", "advanced"],
                index=["beginner", "intermediate", "advanced"].index(
                    st.session_state.prefs.get("experience", "beginner")
                )
            )

            # Focus areas
            st.session_state.prefs["focus"] = st.multiselect(
                "Focus Areas",
                ["glutes", "core", "legs", "shoulders", "back"],
                default=st.session_state.prefs.get("focus", ["glutes", "core"])
            )

            # Available equipment
            st.session_state.prefs["equipment"] = st.multiselect(
                "Available Equipment",
                ["dumbbells", "barbell", "machines", "bands", "bodyweight"],
                default=st.session_state.prefs.get("equipment", ["dumbbells", "machines", "bodyweight"])
            )

            # AI tuning
            st.session_state.ai_tuning["available_days"] = st.slider(
                "Days per week available",
                1, 7,
                st.session_state.ai_tuning.get("available_days", 4)
            )

            st.session_state.ai_tuning["diet"] = st.selectbox(
                "Diet Type",
                ["omnivore", "pescatarian", "vegan"],
                index=["omnivore", "pescatarian", "vegan"].index(
                    st.session_state.ai_tuning.get("diet", "omnivore")
                )
            )

            st.session_state.ai_tuning["protein_target_g"] = st.number_input(
                "Daily Protein Target (g)",
                50, 300,
                st.session_state.ai_tuning.get("protein_target_g", 120)
            )

            st.session_state.ai_tuning["injury_notes"] = st.text_area(
                "Injury Notes (optional)",
                st.session_state.ai_tuning.get("injury_notes", "")
            )

            if st.button("Save Preferences"):
                save_user_progress()
                st.session_state.show_prefs_editor = False
                st.success("Preferences saved!")
                st.rerun()


# ============================================================================
# NEW: STREAK & BADGE FUNCTIONS
# ============================================================================
def compute_streaks(entries):
    """Compute workout streaks from entries"""
    if not entries:
        return {"current": 0, "longest": 0, "last_date": None}

    # Sort entries by date
    sorted_entries = sorted(entries, key=lambda x: x.get("date", ""))

    if not sorted_entries:
        return {"current": 0, "longest": 0, "last_date": None}

    # Simple streak calculation (mock for now)
    current_streak = min(len(sorted_entries), 7)  # Mock current streak
    longest_streak = min(len(sorted_entries), 21)  # Mock longest streak
    last_date = sorted_entries[-1].get("date") if sorted_entries else None

    # Check hydration streak - FIXED with safe access
    hydration7 = False
    weight_entries = st.session_state.get("weight_entries", [])
    if weight_entries:
        recent = weight_entries[-7:]
        if len(recent) >= 7:
            hydration7 = all(e.get("water", 0) >= 2 for e in recent)

    # Count glute sets in last 2 weeks - FIXED with safe access
    glute_sets_2wk = 0
    completed_exercises = st.session_state.get("completed_exercises", [])
    if completed_exercises:
        glute_sets_2wk = sum(
            1 for e in completed_exercises if isinstance(e, str) and ("hip" in e.lower() or "thrust" in e.lower()))

    return {
        "current": current_streak,
        "longest": longest_streak,
        "last_date": last_date,
        "hydration7": hydration7,
        "glute_sets_2wk": glute_sets_2wk
    }


def check_badges(stats):
    """Check which badges are earned based on stats"""
    earned = []
    for badge in BADGES:
        try:
            if badge["rule"](stats):
                earned.append(badge["key"])
        except:
            pass
    return earned


def render_streaks_tab():
    """Render the streaks and badges tab"""
    st.markdown("## ⭐ Streaks & Badges")

    # Calculate streaks - FIXED with safe access
    progress_entries = st.session_state.get("progress_entries", [])
    weight_entries = st.session_state.get("weight_entries", [])
    all_entries = progress_entries + weight_entries
    stats = compute_streaks(all_entries)

    # Display streak counters
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("🔥 Current Streak", f"{stats['current']} days")
    with col2:
        st.metric("🏆 Longest Streak", f"{stats['longest']} days")
    with col3:
        last_date = stats.get("last_date", "Never")
        st.metric("📅 Last Workout", last_date if last_date else "Never")

    st.markdown("---")

    # Display badges
    st.markdown("### 🏅 Your Badges")

    earned_badges = check_badges(stats)
    st.session_state.badges_earned = earned_badges

    # Display earned badges
    badge_cols = st.columns(4)
    for i, badge in enumerate(BADGES):
        with badge_cols[i % 4]:
            if badge["key"] in earned_badges:
                st.success(badge["label"])
            else:
                st.info(f"🔒 {badge['label'].split(' ', 1)[1] if ' ' in badge['label'] else badge['label']}")

    st.markdown("---")

    # Reminder settings - FIXED with safe access
    st.markdown("### ⏰ Workout Reminders")
    st.caption("Reminders are local; for push/email we'll wire a provider later.")

    reminder_prefs = st.session_state.get("reminder_prefs", {"enabled": False, "days": [], "time": "08:00"})

    reminder_enabled = st.checkbox(
        "Enable reminders",
        value=reminder_prefs.get("enabled", False)
    )

    if reminder_enabled:
        # Day selection
        days = st.multiselect(
            "Reminder days",
            ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
            default=reminder_prefs.get("days", [])
        )

        # Time selection
        time = st.time_input(
            "Reminder time",
            value=datetime.strptime(
                reminder_prefs.get("time", "08:00"),
                "%H:%M"
            ).time()
        )

        # Save reminder preferences
        st.session_state.reminder_prefs = {
            "enabled": reminder_enabled,
            "days": days,
            "time": time.strftime("%H:%M")
        }

        if st.button("Save Reminder Settings"):
            save_user_progress()
            st.success("Reminder settings saved!")


# ============================================================================
# NEW: COMMUNITY FUNCTIONS
# ============================================================================
def render_community_tab():
    """Render the community tab"""
    st.markdown("## 👥 Community")

    # Weekly challenge section
    st.markdown("### 🎯 Weekly Challenge")
    challenge = st.selectbox(
        "This week's challenge",
        ["8k steps/day", "3 workouts", "2 core days", "5L water challenge", "No skip week"]
    )

    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input(
            "Display name",
            value=st.session_state.get("display_name", ""),
            key="community_display_name"
        )

    with col2:
        if st.button("Join / Update Challenge"):
            st.session_state.display_name = name
            save_user_progress()
            st.success(f"Joined '{challenge}' as {name}!")

    st.markdown("---")

    # Leaderboard
    st.subheader("🏆 Leaderboard (local device demo)")

    # Mock leaderboard data - FIXED with safe access
    completed_exercises = st.session_state.get("completed_exercises", [])
    leaderboard_data = [
        {"Name": st.session_state.get("display_name", "You"),
         "Points": len(completed_exercises) * 10, "Streak": "🔥 7 days"},
        {"Name": "Sarah M.", "Points": 280, "Streak": "🔥 14 days"},
        {"Name": "Jessica R.", "Points": 220, "Streak": "🔥 5 days"},
        {"Name": "Emma L.", "Points": 190, "Streak": "🔥 3 days"},
    ]

    df = pd.DataFrame(leaderboard_data)
    st.dataframe(df, hide_index=True, use_container_width=True)

    st.markdown("---")

    # Group chat placeholder
    st.markdown("### 💬 Community Chat")

    # Display chat messages - FIXED with safe access
    community_chat = st.session_state.get("community_chat", [])
    for msg in community_chat[-10:]:
        with st.chat_message(msg["role"]):
            st.write(f"**{msg['name']}**: {msg['content']}")

    # Chat input
    chat_input = st.chat_input("Share your progress...")
    if chat_input and st.session_state.get("display_name"):
        if "community_chat" not in st.session_state:
            st.session_state.community_chat = []
        st.session_state.community_chat.append({
            "role": "user",
            "name": st.session_state.display_name,
            "content": chat_input,
            "timestamp": datetime.now().isoformat()
        })
        st.rerun()
    elif chat_input:
        st.warning("Please set your display name first!")

    st.info("Multi-user sync is stubbed for now. Ready for Firebase/Supabase later.")


# ============================================================================
# NEW: DEVICE SYNC FUNCTIONS
# ============================================================================
def fetch_fitbit_demo(client_id, client_secret):
    """Mock Fitbit data fetch"""
    # This is a demo - returns mock data
    import random
    return (
        random.randint(5000, 12000),  # steps
        random.randint(55, 75),  # resting HR
        round(random.uniform(6.5, 8.5), 1)  # sleep hours
    )


def render_devices_tab():
    """Render the devices sync tab"""
    st.markdown("## 🔗 Devices")
    st.caption("Read-only demo. Enter API keys to simulate sync.")

    provider = st.selectbox(
        "Provider",
        ["None", "Fitbit", "Apple Health (manual import)", "Google Fit", "Garmin"]
    )

    if provider == "Fitbit":
        col1, col2 = st.columns(2)
        with col1:
            client_id = st.text_input("FITBIT_CLIENT_ID", key="fitbit_client_id")
        with col2:
            client_secret = st.text_input("FITBIT_CLIENT_SECRET", key="fitbit_client_secret", type="password")

        if st.button("Test fetch (demo)"):
            if client_id and client_secret:
                try:
                    steps, hr, sleep = fetch_fitbit_demo(client_id, client_secret)

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Steps (yesterday)", f"{steps:,}")
                    with col2:
                        st.metric("Resting HR", f"{hr} bpm")
                    with col3:
                        st.metric("Sleep", f"{sleep} hrs")

                    # Store in session state
                    st.session_state.device_metrics = {
                        "steps": steps,
                        "hr": hr,
                        "sleep": sleep,
                        "timestamp": datetime.now().isoformat()
                    }

                    st.success("Demo data fetched! (Not real Fitbit data)")
                except Exception as e:
                    st.error(f"Demo fetch failed: {str(e)}")
            else:
                st.warning("Please enter both Client ID and Secret for demo")

    elif provider == "Apple Health (manual import)":
        uploaded_file = st.file_uploader(
            "Upload Apple Health export (CSV)",
            type=["csv"],
            key="apple_health_upload"
        )
        if uploaded_file:
            st.success("File uploaded! (Processing not implemented in demo)")

    elif provider == "Google Fit":
        st.info("Google Fit integration coming soon!")
        st.text_input("Google API Key (demo)", key="google_fit_key", type="password")

    elif provider == "Garmin":
        st.info("Garmin Connect integration coming soon!")

    st.markdown("---")

    # Display stored metrics - FIXED with safe access
    device_metrics = st.session_state.get("device_metrics", {})
    if device_metrics:
        st.markdown("### 📊 Last Sync")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Steps", f"{device_metrics.get('steps', 0):,}")
        with col2:
            st.metric("Heart Rate", f"{device_metrics.get('hr', 0)} bpm")
        with col3:
            st.metric("Sleep", f"{device_metrics.get('sleep', 0)} hrs")
        st.caption(f"Synced: {device_metrics.get('timestamp', 'Never')}")

    st.info("Production OAuth wiring left as TODO; this tab accepts imports/keys and shows demo metrics.")


# ============================================================================
# NEW: ACCESSIBILITY FUNCTIONS
# ============================================================================
def apply_accessibility_css():
    """Apply accessibility CSS based on user preferences"""
    scale = st.session_state.get("a11y_scale", 1.0)
    theme = st.session_state.get("a11y_theme", "auto")
    reduced_motion = st.session_state.get("a11y_reduced_motion", False)

    css = f"""
    <style>
    :root {{
        --uifx-scale: {scale};
    }}
    .main * {{
        font-size: calc(1rem * var(--uifx-scale));
    }}
    """

    if theme == "high-contrast":
        css += """
        .main {
            background: #000 !important;
            color: #fff !important;
        }
        .stButton button {
            background: #fff !important;
            color: #000 !important;
            border: 2px solid #fff !important;
        }
        """

    if reduced_motion:
        css += """
        * {
            animation-duration: 0.01ms !important;
            transition-duration: 0.01ms !important;
        }
        """

    css += "</style>"
    st.markdown(css, unsafe_allow_html=True)


def i18n(key, lang=None):
    """Simple internationalization helper"""
    if lang is None:
        lang = st.session_state.get("language", "en")

    translations = {
        "en": {
            "welcome": "Welcome to Your Fitness Journey!",
            "workout": "Workout",
            "meal_plan": "Meal Plan",
            "progress": "Progress",
        },
        "es": {
            "welcome": "¡Bienvenido a tu viaje de fitness!",
            "workout": "Entrenamiento",
            "meal_plan": "Plan de comidas",
            "progress": "Progreso",
        },
        "fr": {
            "welcome": "Bienvenue dans votre parcours fitness!",
            "workout": "Entraînement",
            "meal_plan": "Plan de repas",
            "progress": "Progrès",
        }
    }

    return translations.get(lang, translations["en"]).get(key, key)


def render_accessibility_settings():
    """Render accessibility settings in sidebar"""
    with st.expander("♿ Accessibility"):
        # Font size
        st.session_state.a11y_scale = st.slider(
            "Font Size",
            1.0, 1.4,
            st.session_state.get("a11y_scale", 1.0),
            0.1,
            key="font_size_slider"
        )

        # Theme
        st.session_state.a11y_theme = st.selectbox(
            "Color Theme",
            ["auto", "dark", "high-contrast"],
            index=["auto", "dark", "high-contrast"].index(
                st.session_state.get("a11y_theme", "auto")
            ),
            key="theme_select"
        )

        # Reduced motion
        st.session_state.a11y_reduced_motion = st.checkbox(
            "Reduce motion",
            st.session_state.get("a11y_reduced_motion", False),
            key="reduced_motion_check"
        )

        # Language
        st.session_state.language = st.selectbox(
            "Language",
            ["en", "es", "fr"],
            index=["en", "es", "fr"].index(
                st.session_state.get("language", "en")
            ),
            key="language_select"
        )

        if st.button("Apply Settings"):
            save_user_progress()
            st.rerun()


# ============================================================================
# NEW: RICH VIDEO LIBRARY FUNCTIONS
# ============================================================================
def load_videos_db():
    """Load video library database"""
    try:
        if os.path.exists(VIDEOS_DB_JSON):
            with open(VIDEOS_DB_JSON, 'r') as f:
                return json.load(f)
    except:
        pass
    return []


def save_videos_db(db):
    """Save video library database"""
    try:
        with open(VIDEOS_DB_JSON, 'w') as f:
            json.dump(db, f, indent=2)
        return True
    except:
        return False


def add_video_to_library(exercise_key, path, uploader="user"):
    """Add a video to the library"""
    db = load_videos_db()

    # Find or create exercise entry
    exercise_entry = None
    for entry in db:
        if entry["exercise_key"] == exercise_key:
            exercise_entry = entry
            break

    if not exercise_entry:
        exercise_entry = {
            "exercise_key": exercise_key,
            "files": []
        }
        db.append(exercise_entry)

    # Add video
    exercise_entry["files"].append({
        "path": path,
        "uploader": uploader,
        "rating": 0,
        "votes": 0,
        "flagged": False,
        "uploaded_at": datetime.now().isoformat()
    })

    save_videos_db(db)


def rate_video(exercise_key, path, delta):
    """Rate a video in the library"""
    db = load_videos_db()

    for entry in db:
        if entry["exercise_key"] == exercise_key:
            for video in entry["files"]:
                if video["path"] == path:
                    video["votes"] = video.get("votes", 0) + 1
                    current_rating = video.get("rating", 0)
                    # Simple rating update (can be improved)
                    video["rating"] = ((current_rating * (video["votes"] - 1)) + delta) / video["votes"]
                    save_videos_db(db)
                    return True
    return False


def render_video_library(exercise_name, exercise_key):
    """Render video library for an exercise"""
    with st.expander("📹 Video Library"):
        db = load_videos_db()

        # Find videos for this exercise
        videos = []
        for entry in db:
            if entry["exercise_key"] == exercise_key:
                videos = entry.get("files", [])
                break

        # Sort by rating
        videos.sort(key=lambda x: x.get("rating", 0), reverse=True)

        # Show top 3 videos
        if videos:
            st.markdown("**Top Demonstrations:**")
            for i, video in enumerate(videos[:3]):
                col1, col2, col3 = st.columns([3, 1, 1])

                with col1:
                    if os.path.exists(video["path"]):
                        st.video(video["path"])
                    else:
                        st.warning("Video not found")

                with col2:
                    rating = video.get("rating", 0)
                    votes = video.get("votes", 0)
                    st.metric("Rating", f"{rating:.1f} ({votes} votes)")

                with col3:
                    if st.button("👍", key=f"like_{exercise_key}_{i}"):
                        rate_video(exercise_key, video["path"], 5)
                        st.rerun()

                    if st.button("👎", key=f"dislike_{exercise_key}_{i}"):
                        rate_video(exercise_key, video["path"], 1)
                        st.rerun()

                    if st.button("🚩 Report", key=f"report_{exercise_key}_{i}"):
                        video["flagged"] = True
                        save_videos_db(db)
                        st.warning("Video reported")
        else:
            st.info("No videos in library yet. Upload the first one!")

        # Upload new video
        st.markdown("**Upload Alternative Demo:**")
        uploaded = st.file_uploader(
            f"Add video for {exercise_name} (max {MAX_VIDEO_MB} MB)",
            type=['mp4', 'mov', 'avi', 'webm'],
            key=f"library_upload_{exercise_key}"
        )

        if uploaded and st.button("Add to Library", key=f"add_library_{exercise_key}"):
            # Check file size
            if uploaded.size / (1024 * 1024) > MAX_VIDEO_MB:
                st.error(f"File exceeds {MAX_VIDEO_MB} MB limit!")
            else:
                # Save video
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{exercise_key}_lib_{timestamp}_{uploaded.name}"
                filepath = os.path.join(EXERCISE_VIDEOS_DIR, filename)

                with open(filepath, 'wb') as f:
                    f.write(uploaded.getbuffer())

                add_video_to_library(
                    exercise_key,
                    filepath,
                    st.session_state.get("display_name", "user")
                )

                st.success("Video added to library!")
                st.rerun()


# ============================================================================
# EXISTING VIDEO MANAGEMENT FUNCTIONS (UNCHANGED)
# ============================================================================
def load_videos_json():
    """Load video mappings from videos.json"""
    try:
        if os.path.exists(VIDEOS_JSON):
            with open(VIDEOS_JSON, 'r') as f:
                return json.load(f)
    except Exception as e:
        st.error(f"Error loading videos: {str(e)}")
    return {}


def save_videos_json(videos_dict):
    """Save video mappings to videos.json"""
    if not ADMIN_UI:
        st.warning("Uploads are disabled.")
        return False
    try:
        with open(VIDEOS_JSON, 'w') as f:
            json.dump(videos_dict, f, indent=2)
        return True
    except Exception as e:
        st.error(f"Error saving videos: {str(e)}")
        return False


def get_exercise_id(exercise_name):
    """Generate a stable exercise ID from name"""
    return re.sub(r'[^a-z0-9]+', '_', exercise_name.lower()).strip('_')


def render_admin_intro_video_manager():
    """Simplified admin interface for intro video only"""
    if not ADMIN_UI:
        return
    videos = load_videos_json()

    source_type = st.selectbox(
        "Video source",
        ["URL", "Upload File"],
        key="intro_source_simple"
    )

    if source_type == "URL":
        intro_url = st.text_input(
            "YouTube or Video URL",
            value=videos.get("__intro__", ""),
            key="intro_url_simple"
        )
        if st.button("Save Video URL", key="save_intro_url_simple"):
            videos["__intro__"] = intro_url
            if save_videos_json(videos):
                st.success("Intro video URL saved!")
                st.rerun()
    else:
        uploaded_intro = st.file_uploader(
            "Upload intro video (MP4 or MOV)",
            type=['mp4', 'mov'],
            key="intro_file_simple"
        )
        if uploaded_intro and st.button("Save Intro Video", key="save_intro_file_simple"):
            try:
                video_path = os.path.join(VIDEOS_DIR, f"intro_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4")
                with open(video_path, 'wb') as f:
                    f.write(uploaded_intro.getbuffer())
                videos["__intro__"] = video_path
                if save_videos_json(videos):
                    st.success("Intro video uploaded!")
                    st.rerun()
            except Exception as e:
                st.error(f"Upload failed: {str(e)}")

    if "__intro__" in videos:
        if st.button("Remove Intro Video", key="remove_intro_simple"):
            del videos["__intro__"]
            save_videos_json(videos)
            st.success("Intro video removed")
            st.rerun()


def render_admin_video_manager():
    """Render admin-only video management panel"""
    if not ADMIN_UI:
        return

    with st.expander("🔧 Admin: Video Manager"):
        st.markdown("### Video Management")

        videos = load_videos_json()

        # Manage intro video
        st.markdown("#### Homepage Intro Video")
        intro_col1, intro_col2 = st.columns(2)

        with intro_col1:
            intro_source = st.selectbox(
                "Source type for intro",
                ["URL", "Upload File"],
                key="intro_source_type"
            )

            if intro_source == "URL":
                intro_url = st.text_input(
                    "Video URL",
                    value=videos.get("__intro__", ""),
                    key="intro_url_input"
                )
                if st.button("Save Intro URL", key="save_intro_url"):
                    videos["__intro__"] = intro_url
                    if save_videos_json(videos):
                        st.success("Intro video URL saved!")
                        st.rerun()
            else:
                uploaded_intro = st.file_uploader(
                    "Upload intro video",
                    type=['mp4', 'mov'],
                    key="intro_file_upload"
                )
                if uploaded_intro and st.button("Save Intro File", key="save_intro_file"):
                    try:
                        video_path = os.path.join(VIDEOS_DIR, f"intro_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4")
                        with open(video_path, 'wb') as f:
                            f.write(uploaded_intro.getbuffer())
                        videos["__intro__"] = video_path
                        if save_videos_json(videos):
                            st.success("Intro video uploaded!")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Upload failed: {str(e)}")

        with intro_col2:
            if "__intro__" in videos:
                st.info(f"Current: {videos['__intro__'][:50]}...")
                if st.button("Remove Intro Video", key="remove_intro"):
                    del videos["__intro__"]
                    save_videos_json(videos)
                    st.rerun()

        st.markdown("---")

        # Manage exercise videos
        st.markdown("#### Exercise Videos")

        all_exercises = get_all_exercises()

        exercise_name = st.selectbox(
            "Select exercise",
            [""] + all_exercises,
            key="admin_exercise_select"
        )

        if exercise_name:
            exercise_id = get_exercise_id(exercise_name)

            col1, col2 = st.columns(2)

            with col1:
                source_type = st.selectbox(
                    "Source type",
                    ["URL", "Upload File"],
                    key=f"source_type_{exercise_id}"
                )

                if source_type == "URL":
                    video_url = st.text_input(
                        "Video URL",
                        value=videos.get(exercise_id, ""),
                        key=f"url_{exercise_id}"
                    )
                    if st.button("Save URL", key=f"save_url_{exercise_id}"):
                        videos[exercise_id] = video_url
                        if save_videos_json(videos):
                            st.success(f"Video URL saved for {exercise_name}!")
                            st.rerun()
                else:
                    uploaded_file = st.file_uploader(
                        "Upload video",
                        type=['mp4', 'mov'],
                        key=f"upload_{exercise_id}"
                    )
                    if uploaded_file and st.button("Save File", key=f"save_file_{exercise_id}"):
                        try:
                            video_path = os.path.join(VIDEOS_DIR,
                                                      f"{exercise_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4")
                            with open(video_path, 'wb') as f:
                                f.write(uploaded_file.getbuffer())
                            videos[exercise_id] = video_path
                            if save_videos_json(videos):
                                st.success(f"Video uploaded for {exercise_name}!")
                                st.rerun()
                        except Exception as e:
                            st.error(f"Upload failed: {str(e)}")

            with col2:
                if exercise_id in videos:
                    st.info(f"Current: {videos[exercise_id][:50]}...")
                    if st.button("Remove Video", key=f"remove_{exercise_id}"):
                        del videos[exercise_id]
                        save_videos_json(videos)
                        st.rerun()


def get_all_exercises():
    """Get list of all unique exercise names"""
    exercises = set()

    # Add all exercises from workout data
    for ex in BOOTY_L1 + ABS_CORE_ONLY:
        if ex.get("name") and ex["name"] != "Repeat 2x total":
            exercises.add(ex["name"])

    # Add more exercises
    basic_exercises = [
        "Hip Thrust", "RDLs (Romanian Deadlifts)", "Kickbacks", "Hyperextensions",
        "Bulgarian Split Squats", "Leg Press", "Leg Curl", "Lat Pulldown Wide Grip"
    ]
    exercises.update(basic_exercises)

    return sorted(list(exercises))


# ============================================================================
# WORKOUT LOG FUNCTIONS (NEW)
# ============================================================================
def save_workout_log(date_str, exercise_id, exercise_name, set_num, reps, weight, completed):
    """Save workout data to CSV"""
    try:
        new_entry = pd.DataFrame([{
            'date': date_str,
            'exercise_id': exercise_id,
            'exercise': exercise_name,
            'set': set_num,
            'reps': reps,
            'weight': weight,
            'completed': completed
        }])

        if os.path.exists(WORKOUT_LOG_CSV):
            existing_df = pd.read_csv(WORKOUT_LOG_CSV)
            updated_df = pd.concat([existing_df, new_entry], ignore_index=True)
        else:
            updated_df = new_entry

        updated_df.to_csv(WORKOUT_LOG_CSV, index=False)
        return True
    except Exception as e:
        st.error(f"Error saving workout log: {str(e)}")
        return False


def get_today_workout_log(date_str, exercise_id):
    """Get today's workout log for specific exercise"""
    try:
        if os.path.exists(WORKOUT_LOG_CSV):
            df = pd.read_csv(WORKOUT_LOG_CSV)
            filtered = df[(df['date'] == date_str) & (df['exercise_id'] == exercise_id)]
            return filtered
    except Exception as e:
        st.error(f"Error reading workout log: {str(e)}")
    return pd.DataFrame()


def parse_set_count(sets_string):
    """Parse set count from string - allow up to 15"""
    if not sets_string or sets_string.strip() == "—":
        return 0

    # Check if it's a number
    try:
        num = int(sets_string)
        return min(num, 15)  # Cap at 15
    except:
        pass

    s = sets_string.lower()
    s = re.sub(r'\d+\s*warm[- ]*up.*?(?:\+|$)', '', s)
    nums = re.findall(r'\d+', s)

    if not nums:
        return 1 if "set" in s else 0

    total = sum(int(n) for n in nums)
    return min(total, 15)  # Cap at 15


def save_exercise_video(uploaded_file, key_slug):
    """Save an exercise video with 50MB limit"""
    try:
        # Check file size
        file_size = uploaded_file.size / (1024 * 1024)  # Convert to MB
        if file_size > MAX_VIDEO_MB:
            st.error(f"Video file is {file_size:.1f} MB, exceeds {MAX_VIDEO_MB} MB limit!")
            return None

        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{key_slug}_{timestamp}_{uploaded_file.name}"
        filepath = os.path.join(EXERCISE_VIDEOS_DIR, filename)

        # Save file
        with open(filepath, 'wb') as f:
            f.write(uploaded_file.getbuffer())

        return filepath
    except Exception as e:
        st.error(f"Error saving video: {str(e)}")
        return None


def find_exercise_video(key_slug):
    """Find the most recent video for an exercise"""
    try:
        if not os.path.exists(EXERCISE_VIDEOS_DIR):
            return None

        # Look for files matching the key_slug pattern
        pattern = f"{key_slug}_*"
        files = []
        for f in os.listdir(EXERCISE_VIDEOS_DIR):
            if f.startswith(f"{key_slug}_"):
                files.append(os.path.join(EXERCISE_VIDEOS_DIR, f))

        if files:
            # Return the most recent file
            return max(files, key=os.path.getmtime)
    except Exception as e:
        st.error(f"Error finding video: {str(e)}")
    return None


def render_enhanced_exercise_card(exercise, idx, workout_date):
    """Enhanced exercise card with video and set tracking"""
    exercise_name = exercise['name']
    exercise_id = get_exercise_id(exercise_name)
    sets_info = exercise.get('sets', '—')
    reps_info = exercise.get('reps', '—')
    category = exercise.get('category', 'General')
    exercise_key = f"{exercise_id}_{workout_date}"

    num_sets = parse_set_count(sets_info)

    with st.container():
        st.markdown(f"### {idx}. {exercise_name}")
        st.markdown(f"**Category:** {category} | **Sets:** {sets_info} | **Reps:** {reps_info}")

        # NEW: Exercise alternatives
        alternatives = EXERCISE_ALTERNATIVES.get(exercise_id, {})
        if alternatives:
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🏠 At-home variant", key=f"home_{exercise_key}"):
                    st.info("At-home alternatives: " + ", ".join(alternatives.get("at_home", ["None available"])))
            with col2:
                if st.button("🦵 Low-impact alternative", key=f"low_{exercise_key}"):
                    st.info("Low-impact alternatives: " + ", ".join(alternatives.get("low_impact", ["None available"])))

        col1, col2 = st.columns([1, 1])

        # Left column: Set/Rep tracker - FIXED with safe access
        with col1:
            if num_sets > 0:
                st.markdown("#### 📝 Track Your Sets")

                workout_sets = st.session_state.get("workout_sets", {})
                sets_data = []
                # Check if this is a time-based exercise (warm-up with seconds)
                is_time_based = "second" in reps_info.lower() and category == "Warm-up"

                for set_num in range(1, num_sets + 1):
                    with st.container():
                        cols = st.columns([1, 2, 2, 1])

                        with cols[0]:
                            st.markdown(f"**Set {set_num}**")

                        with cols[1]:
                            if is_time_based:
                                # For time-based warm-up exercises, show seconds tracker
                                time_key = f"{exercise_id}_{workout_date}_set{set_num}_time"
                                seconds = st.number_input(
                                    "Seconds",
                                    min_value=0,
                                    max_value=120,
                                    value=workout_sets.get(time_key, 60),
                                    step=5,
                                    key=time_key,
                                    label_visibility="collapsed"
                                )
                                st.session_state.workout_sets[time_key] = seconds
                                reps = seconds  # Store as reps for consistency
                            else:
                                # Regular reps tracking for non-warmup exercises
                                reps_key = f"{exercise_id}_{workout_date}_set{set_num}_reps"
                                reps = st.number_input(
                                    "Reps",
                                    min_value=0,
                                    max_value=100,
                                    value=workout_sets.get(reps_key, 10),
                                    key=reps_key,
                                    label_visibility="collapsed"
                                )
                                st.session_state.workout_sets[reps_key] = reps

                        with cols[2]:
                            if is_time_based:
                                # No weight for time-based warm-ups
                                st.markdown("*No weight*")
                                weight = 0.0
                            else:
                                # Regular weight tracking for non-warmup exercises
                                weight_key = f"{exercise_id}_{workout_date}_set{set_num}_weight"
                                weight = st.number_input(
                                    "Weight (lbs)",
                                    min_value=0.0,
                                    max_value=500.0,
                                    value=workout_sets.get(weight_key, 0.0),
                                    step=2.5,
                                    key=weight_key,
                                    label_visibility="collapsed"
                                )
                                st.session_state.workout_sets[weight_key] = weight

                        with cols[3]:
                            completed_key = f"{exercise_id}_{workout_date}_set{set_num}_completed"
                            completed = st.checkbox(
                                "✅",
                                key=completed_key,
                                value=workout_sets.get(completed_key, False)
                            )
                            st.session_state.workout_sets[completed_key] = completed

                        sets_data.append({
                            'set': set_num,
                            'reps': reps,
                            'weight': weight,
                            'completed': completed
                        })
                if st.button(f"💾 Save {exercise_name}", key=f"save_{exercise_id}_{workout_date}"):
                    saved_count = 0
                    for data in sets_data:
                        if save_workout_log(
                                workout_date,
                                exercise_id,
                                exercise_name,
                                data['set'],
                                data['reps'],
                                data['weight'],
                                data['completed']
                        ):
                            saved_count += 1

                    if saved_count > 0:
                        st.success(f"Saved {saved_count} sets!")

                        today_log = get_today_workout_log(workout_date, exercise_id)
                        if not today_log.empty:
                            st.markdown("##### Today's Log")
                            st.dataframe(
                                today_log[['set', 'reps', 'weight', 'completed']],
                                hide_index=True,
                                use_container_width=True
                            )
            else:
                # Simple checkbox for exercises without sets
                key = f"ex_{idx}_{exercise_name.replace(' ', '_')}"
                completed = st.checkbox("✅ Done", key=key)

                if completed:
                    if "completed_exercises" not in st.session_state:
                        st.session_state.completed_exercises = []
                    if key not in st.session_state.completed_exercises:
                        st.session_state.completed_exercises.append(key)

        # Right column: Video
        with col2:
            st.markdown("#### 🎥 Exercise Demo")

            # Check for uploaded exercise-specific video first
            existing_video = find_exercise_video(exercise_key)

            if existing_video:
                try:
                    st.video(existing_video)
                    if st.button(f"Delete video", key=f"delete_video_{exercise_key}"):
                        try:
                            os.remove(existing_video)
                            st.success("Video deleted!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error deleting video: {str(e)}")
                except Exception as e:
                    st.error(f"Error loading video: {str(e)}")
            else:
                # Check for general exercise videos from videos.json
                videos = load_videos_json()
                src = videos.get(exercise_id)

                if src:
                    try:
                        if src.startswith(("http://", "https://")):
                            st.video(src)
                        elif os.path.exists(src):
                            with open(src, 'rb') as video_file:
                                video_bytes = video_file.read()
                                st.video(video_bytes)
                        else:
                            st.info("Video file not found. Contact admin to update.")
                    except Exception as e:
                        st.error(f"Error loading video: {str(e)}")
                else:
                    st.info("No video available for this exercise yet.")

            # Video upload section
            with st.expander("📹 Upload Demo Video"):
                uploaded_file = st.file_uploader(
                    f"Upload video for {exercise_name} (max {MAX_VIDEO_MB} MB)",
                    type=['mp4', 'mov', 'avi', 'webm'],
                    key=f"upload_{exercise_key}"
                )

                if uploaded_file and st.button(f"Save Video", key=f"save_{exercise_key}"):
                    saved_path = save_exercise_video(uploaded_file, exercise_key)
                    if saved_path:
                        st.success("Video saved!")
                        st.rerun()

            # NEW: Video library
            render_video_library(exercise_name, exercise_key)

            # Admin-only controls for general videos
            if ADMIN_UI:
                with st.expander(f"🔧 Admin: Set General Video", expanded=False):
                    uploaded_file = st.file_uploader(
                        "Upload MP4/MOV",
                        type=['mp4', 'mov', "m4v"],
                        key=f"admin_upload_{exercise_id}"
                    )
                    video_url = st.text_input(
                        "...or paste a video URL",
                        value=src if src and src.startswith("http") else "",
                        key=f"admin_url_{exercise_id}"
                    )

                    b1, b2 = st.columns(2)
                    with b1:
                        if st.button("Save Video", key=f"admin_save_{exercise_id}", type="primary"):
                            source_to_save = None
                            if uploaded_file:
                                try:
                                    video_path = os.path.join(VIDEOS_DIR,
                                                              f"{exercise_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4")
                                    with open(video_path, 'wb') as f:
                                        f.write(uploaded_file.getbuffer())
                                    source_to_save = video_path
                                except Exception as e:
                                    st.error(f"Upload failed: {str(e)}")
                            elif video_url:
                                source_to_save = video_url

                            if source_to_save:
                                videos[exercise_id] = source_to_save
                                if save_videos_json(videos):
                                    st.success(f"Video saved for {exercise_name}!")
                                    st.rerun()
                            else:
                                st.warning("Please upload a file or provide a URL.")
                    with b2:
                        if src and st.button("Delete Video", key=f"admin_delete_{exercise_id}"):
                            if exercise_id in videos:
                                del videos[exercise_id]
                                if save_videos_json(videos):
                                    st.success(f"Video removed for {exercise_name}.")
                                    st.rerun()


def render_homepage_intro_video():
    """Render intro video at bottom of homepage with admin controls."""
    videos = load_videos_json()
    src = videos.get("__intro__")

    st.markdown("---")
    st.markdown("### 🎥 Welcome Video")

    # Viewer: always allowed to watch
    _, col_vid, _ = st.columns([1, 2, 1])
    with col_vid:
        if src:
            try:
                if src.startswith(("http://", "https://")):
                    st.video(src)
                elif os.path.exists(src):
                    st.video(src)
                else:
                    st.info("Welcome video file not found.")
            except Exception as e:
                st.error(f"Error loading video: {str(e)}")
        else:
            st.info("Welcome video has not been set yet.")

    # Admin-only controls
    if ADMIN_UI:
        with st.expander("🔧 Admin: Set / Change Welcome Video", expanded=False):
            up = st.file_uploader("Upload MP4/MOV/M4V", type=["mp4", "mov", "m4v"], key="admin_intro_upload")
            url = st.text_input("...or paste a video URL", placeholder="https://youtube.com/...", key="admin_intro_url")

            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("Save Video", type="primary", key="admin_intro_save"):
                    source_to_save = None
                    if up:
                        try:
                            video_path = os.path.join(VIDEOS_DIR,
                                                      f"intro_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4")
                            with open(video_path, 'wb') as f:
                                f.write(up.getbuffer())
                            source_to_save = video_path
                        except Exception as e:
                            st.error(f"Upload failed: {str(e)}")
                    elif url:
                        source_to_save = url

                    if source_to_save:
                        videos["__intro__"] = source_to_save
                        if save_videos_json(videos):
                            st.success("Saved welcome video.")
                            st.rerun()
                    else:
                        st.warning("Please upload a file or provide a URL.")
            with col2:
                if src and st.button("Delete Video", key="admin_intro_delete"):
                    if "__intro__" in videos:
                        del videos["__intro__"]
                        if save_videos_json(videos):
                            st.success("Deleted welcome video.")
                            st.rerun()


# ============================================================================
# COACH JO CHATBOT FUNCTIONS (NEW - LLM VERSION) - FIXED
# ============================================================================
SYSTEM_PROMPT = (
    "You are Coach Jo, a practical fitness assistant focused on glute growth, progressive overload, "
    "protein targets, vegan/pescatarian/omnivore swaps, plus creatine & hydration best practices. "
    "Answer concisely and safely. This is not medical advice."
)


def resolve_provider():
    """Automatically detect which provider to use based on available API keys"""
    import os

    # Check for API keys in environment or secrets
    openai_key = os.environ.get("OPENAI_API_KEY", "")
    if not openai_key:
        try:
            openai_key = st.secrets.get("OPENAI_API_KEY", "")
        except:
            pass

    gemini_key = os.environ.get("GEMINI_API_KEY", "")
    if not gemini_key:
        try:
            gemini_key = st.secrets.get("GEMINI_API_KEY", "")
        except:
            pass

    # Return the first available provider
    if openai_key:
        return "openai"
    elif gemini_key:
        return "gemini"
    else:
        return None


def _send_to_coach(user_text: str):
    """Send message to coach - FIXED to auto-detect provider"""
    # Ensure coach_history exists
    if "coach_history" not in st.session_state:
        st.session_state.coach_history = []

    st.session_state.coach_history.append({"role": "user", "content": user_text})

    provider = resolve_provider()

    if not provider:
        answer = "AI assistant isn't configured yet. Please add OPENAI_API_KEY or GEMINI_API_KEY to environment variables or Streamlit secrets."
    else:
        try:
            answer = ask_coach_llm(
                messages=[{"role": "system", "content": SYSTEM_PROMPT}] + st.session_state.coach_history,
                provider=provider
            )
        except Exception as e:
            answer = f"Sorry, I couldn't get a response. Please check your API key configuration and try again."

    st.session_state.coach_history.append({"role": "assistant", "content": answer})
    st.rerun()


def ask_coach_llm(messages: list, provider: str) -> str:
    """Call the appropriate LLM provider"""
    import os
    provider = (provider or "").lower()

    if provider.startswith("gemini"):
        # Google Generative AI
        try:
            import google.generativeai as genai
        except ImportError:
            return "Please install google-generativeai: pip install google-generativeai"

        # Check environment variable first, then Streamlit secrets
        key = os.environ.get("GEMINI_API_KEY", "")
        if not key:
            try:
                key = st.secrets.get("GEMINI_API_KEY", "")
            except:
                pass
        if not key:
            raise RuntimeError("GEMINI_API_KEY not set. Please set it in environment variables or Streamlit secrets.")

        genai.configure(api_key=key)
        prompt = "\n\n".join([f"{m['role'].upper()}: {m['content']}" for m in messages])
        model = genai.GenerativeModel("gemini-1.5-pro")
        resp = model.generate_content(prompt)
        return (getattr(resp, "text", None) or resp.candidates[0].content.parts[0].text).strip()

    else:
        # OpenAI
        try:
            from openai import OpenAI
        except ImportError:
            return "Please install openai: pip install openai"

        # Check environment variable first, then Streamlit secrets
        key = os.environ.get("OPENAI_API_KEY", "")
        if not key:
            try:
                key = st.secrets.get("OPENAI_API_KEY", "")
            except:
                pass
        if not key:
            raise RuntimeError("OPENAI_API_KEY not set. Please set it in environment variables or Streamlit secrets.")

        client = OpenAI(api_key=key)
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": m["role"], "content": m["content"]} for m in messages],
            temperature=0.5,
            max_tokens=700,
        )
        return resp.choices[0].message.content.strip()


def render_coach_jo_tab():
    """Render the Coach Jo chatbot tab with LLM support - FIXED"""
    # Ensure coach_history exists
    if 'coach_history' not in st.session_state:
        st.session_state.coach_history = []

    st.subheader("💬 Coach Jo — Your Fitness Assistant")
    st.caption(
        "Powered by AI. Ask about meal swaps, protein targets, creatine, hydration, progressive overload, or substitutions. Not medical advice.")

    # Check if provider is available
    provider = resolve_provider()

    if not provider:
        st.warning(
            "⚠️ AI assistant isn't configured yet. Add OPENAI_API_KEY or GEMINI_API_KEY to environment variables or Streamlit secrets to enable Coach Jo.")
        return

    # Starter chips
    c1, c2, c3 = st.columns(3)
    if c1.button("Swap salmon dinner → vegan (40g protein)", use_container_width=True):
        _send_to_coach("How can I swap a salmon dinner to a vegan dinner with ~40g protein?")
    if c2.button("Hip thrust progression (12 reps felt easy)", use_container_width=True):
        _send_to_coach("I hit 12 reps on hip thrusts; how should I progress weight and reps?")
    if c3.button("Alternative to Bulgarian split squats", use_container_width=True):
        _send_to_coach("What are alternatives to Bulgarian split squats that still hit glutes well?")

    # Chat transcript - FIXED with safe access
    for m in st.session_state.get('coach_history', []):
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    # Chat input
    user_msg = st.chat_input("Ask Coach Jo...")
    if user_msg:
        _send_to_coach(user_msg)
# ============================================================================
# STYLES
# ============================================================================
def load_styles():
    """Load custom CSS styles"""
    st.markdown("""
    <style>
        .main {
            background: linear-gradient(135deg, #ffeef8 0%, #fff5f8 50%, #f0f8ff 100%);
        }
        .main-header {
            font-size: 3rem;
            font-weight: 800;
            text-align: center;
            background: linear-gradient(45deg, #FF1493, #FF69B4, #DA70D6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
            margin-bottom: .5rem;
        }
        .sub-header {
            font-size: 1.1rem;
            text-align: center;
            color: #666;
            margin-bottom: 1rem;
            font-weight: 300;
        }
        .hero-section {
            text-align: center;
            padding: 2rem;
            background: linear-gradient(135deg, rgba(255,20,147,.15), rgba(255,105,180,.15), rgba(218,112,214,.15));
            border-radius: 18px;
            margin-bottom: 20px;
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px rgba(0,0,0,.08);
            border: 1px solid rgba(255,255,255,.35);
        }
        .nav-button {
            background: linear-gradient(135deg, #FF69B4, #DA70D6);
            color: white;
            padding: 1.5rem;
            border-radius: 15px;
            text-align: center;
            font-size: 1.2rem;
            font-weight: 600;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            transition: transform 0.2s;
            cursor: pointer;
        }
        .nav-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0,0,0,0.15);
        }
        .info-card {
            background: white;
            padding: 1.5rem;
            border-radius: 12px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 1rem;
        }
        .weekly-box {
            background: rgba(255,255,255,.96);
            padding: 12px;
            border-radius: 14px;
            margin: 8px 0 14px 0;
            box-shadow: 0 4px 15px rgba(0,0,0,.08);
            border-left: 5px solid #FF1493;
        }
        .category-header {
            background: linear-gradient(45deg,#FF69B4,#DA70D6);
            color:#fff;
            padding: 10px;
            border-radius: 10px;
            text-align:center;
            font-weight:700;
            margin: 12px 0 8px 0;
        }
        .exercise-card {
            background: rgba(255,255,255,.98);
            padding: 12px;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0,0,0,.08);
            margin: 8px 0;
            border-left: 5px solid #FF1493;
        }
        .completed-card {
            background: rgba(232,245,232,.95);
            border-left: 5px solid #4CAF50;
        }
        .badge {
            display:inline-block;
            padding:6px 10px;
            border-radius:12px;
            color:#fff;
            font-weight:700;
            margin:6px 0;
        }
    </style>
    """, unsafe_allow_html=True)


# ============================================================================
# WORKOUT DATA
# ============================================================================
# ============================================================================
# WORKOUT DATA - UPDATED FROM WORD DOCUMENT
# ============================================================================
PROGRAM_SPLIT = {
    "Level 1": {
        "Monday": "BOOTY",
        "Tuesday": "LIGHT SHOULDERS & BACK",
        "Wednesday": "CARDIO",
        "Thursday": "LEGS & BOOTY",
        "Friday": "SHOULDERS & ABS/CORE",
        "Saturday": "LIGHT SHOULDERS & BACK",
        "Sunday": "REST"
    },
    "Level 2": {
        "Monday": "BOOTY A",
        "Tuesday": "LIGHT SHOULDERS & BACK",
        "Wednesday": "CARDIO",
        "Thursday": "BOOTY B",
        "Friday": "SHOULDERS & ABS/CORE",
        "Saturday": "LEGS & BOOTY",
        "Sunday": "REST"
    }
}

# Level 1 Monday - BOOTY
BOOTY_L1_MONDAY = [
    # Individual warm-up exercises
    {"name": "🦘 Squat Jump", "sets": "2", "reps": "30 seconds each", "category": "Warm-up"},
    {"name": "🏃 High Knees", "sets": "1", "reps": "60 seconds", "category": "Warm-up"},
    {"name": "⭐ Jumping Jack", "sets": "1", "reps": "60 seconds", "category": "Warm-up"},
    {"name": "🦵 High Kicks", "sets": "1", "reps": "60 seconds", "category": "Warm-up"},
    {"name": "🔄 Forward Leg Swings", "sets": "1 left + 1 right", "reps": "30 seconds each leg", "category": "Warm-up"},
    {"name": "Kickbacks", "sets": "1 warm up + 3 each side", "reps": "10-12; 12-15 last set", "category": "Booty"},
    {"name": "Hip Thrust", "sets": "1 warm up + 3 + 1 AMRAP", "reps": "10-12; 8 last set; AMRAP ~20%", "category": "Booty"},
    {"name": "Hyperextensions", "sets": "1 warm up + 3 + 1 AMRAP", "reps": "10-12; 10s hold last rep", "category": "Booty"},
    {"name": "RDLs (Romanian Deadlifts)", "sets": "1 warm up + 3", "reps": "10-12; 8 last set", "category": "Booty"},
    {"name": "Stairmaster", "sets": "—", "reps": "30 min fat loss levels 8-10", "category": "Cardio"},
    {"name": "Stretching", "sets": "—", "reps": "5 min", "category": "Recovery"}
]

# Level 2 Monday - BOOTY A
BOOTY_L2_MONDAY = [
    # Individual warm-up exercises (same as Level 1)
    {"name": "🦘 Squat Jump", "sets": "2", "reps": "30 seconds each", "category": "Warm-up"},
    {"name": "🏃 High Knees", "sets": "1", "reps": "60 seconds", "category": "Warm-up"},
    {"name": "⭐ Jumping Jack", "sets": "1", "reps": "60 seconds", "category": "Warm-up"},
    {"name": "🦵 High Kicks", "sets": "1", "reps": "60 seconds", "category": "Warm-up"},
    {"name": "🔄 Forward Leg Swings", "sets": "1 left + 1 right", "reps": "30 seconds each leg", "category": "Warm-up"},
    {"name": "Kickbacks", "sets": "1 warm up + 3 each side", "reps": "10-12; 12-15 last set", "category": "Booty"},
    {"name": "Hip Thrust", "sets": "1 warm up + 3 + 1 AMRAP", "reps": "10-12; 8 last set; AMRAP ~20%", "category": "Booty"},
    {"name": "Hyperextensions", "sets": "1 warm up + 3 + 1 AMRAP", "reps": "10-12; 10s hold last rep", "category": "Booty"},
    {"name": "RDLs (Romanian Deadlifts)", "sets": "1 warm up + 3", "reps": "10-12; 8 last set", "category": "Booty"},
    {"name": "Stairmaster", "sets": "—", "reps": "30 min fat loss levels 8-10", "category": "Cardio"},
    {"name": "Stretching", "sets": "—", "reps": "5 min", "category": "Recovery"}
]

# Tuesday - LIGHT SHOULDERS & BACK (Same for L1 and L2)
SHOULDERS_BACK_LIGHT = [
    {"name": "Lat Pulldown Wide Grip", "sets": "1 warm up + 3", "reps": "10-12", "category": "Back"},
    {"name": "Seated Row Close Grip", "sets": "1 warm up + 3", "reps": "10-12", "category": "Back"},
    {"name": "Overhead Press", "sets": "1 warm up + 3", "reps": "10-12", "category": "Shoulders"},
    {"name": "Lateral Raises", "sets": "3", "reps": "12-15", "category": "Shoulders"},
    {"name": "Face Pulls", "sets": "3", "reps": "15-20", "category": "Shoulders"}
]

# Wednesday - CARDIO (Both levels)
CARDIO_WEDNESDAY = [
    {"name": "Stairmaster", "sets": "—", "reps": "30-45 min intervals", "category": "Cardio"},
    {"name": "Treadmill Incline Walk", "sets": "—", "reps": "Alternative: 30 min", "category": "Cardio"}
]

# Thursday Level 1 - LEGS & BOOTY
LEGS_BOOTY_L1_THURSDAY = [
    {"name": "🔄 Reverse Lunge to Knee Drive", "sets": "1", "reps": "12-15 reps each leg (60 sec)",
     "category": "Warm-up"},
    {"name": "🦵 Side-to-Side Squat Walk (with band)", "sets": "2", "reps": "30 seconds each", "category": "Warm-up"},
    {"name": "🌉 Banded Glute Bridge March", "sets": "2", "reps": "30 seconds each", "category": "Warm-up"},
    {"name": "Leg Press", "sets": "1 warm up + 3", "reps": "10-12", "category": "Legs"},
    {"name": "Bulgarian Split Squats", "sets": "3 each leg", "reps": "10-12", "category": "Legs"},
    {"name": "Leg Curls", "sets": "3", "reps": "10-12", "category": "Legs"},
    {"name": "Cable Kickbacks", "sets": "3 each leg", "reps": "12-15", "category": "Booty"},
    {"name": "Walking Lunges", "sets": "3", "reps": "20 total", "category": "Legs"}
]

# Thursday Level 2 - BOOTY B
BOOTY_L2_THURSDAY = [
    # Individual warm-up exercises for BOOTY B
    {"name": "🔄 Reverse Lunge to Knee Drive", "sets": "1", "reps": "12-15 reps each leg (60 sec)", "category": "Warm-up"},
    {"name": "🦵 Side-to-Side Squat Walk (with band)", "sets": "2", "reps": "30 seconds each", "category": "Warm-up"},
    {"name": "🌉 Banded Glute Bridge March", "sets": "2", "reps": "30 seconds each", "category": "Warm-up"},
    {"name": "Kickbacks", "sets": "1 warm up + 3 each side", "reps": "10-12; 12-15 last set", "category": "Booty"},
    {"name": "Hip Thrust", "sets": "1 warm up + 3 + 1 AMRAP", "reps": "10-12; 8 last set; AMRAP ~20%", "category": "Booty"},
    {"name": "Hyperextensions", "sets": "1 warm up + 3 + 1 AMRAP", "reps": "10-12; 10s hold last rep", "category": "Booty"},
    {"name": "RDLs (Romanian Deadlifts)", "sets": "1 warm up + 3", "reps": "10-12; 8 last set", "category": "Booty"},
    {"name": "Abductors", "sets": "1 warm up + 3", "reps": "10-12; 8 last set", "category": "Booty"},
    {"name": "Leg Finisher: Single Leg Hip Thrust, Sumo Squats, Squat Jump", "sets": "1 set (each side) + 3", "reps": "8-10; 1 set", "category": "Booty"},
    {"name": "Stretching", "sets": "—", "reps": "5 min", "category": "Recovery"}
]

# Friday - SHOULDERS & ABS/CORE (Both levels)
SHOULDERS_ABS_FRIDAY = [
    {"name": "Shoulder Press", "sets": "1 warm up + 3", "reps": "10-12", "category": "Shoulders"},
    {"name": "Lateral Raises", "sets": "3", "reps": "12-15", "category": "Shoulders"},
    {"name": "Rear Delt Flyes", "sets": "3", "reps": "12-15", "category": "Shoulders"},
    {"name": "Plank", "sets": "3", "reps": "60 sec", "category": "Core"},
    {"name": "Russian Twists", "sets": "3", "reps": "30", "category": "Core"},
    {"name": "Leg Raises", "sets": "3", "reps": "15", "category": "Core"}
]

# Saturday Level 1 - Repeat Tuesday workout
# Saturday Level 2 - LEGS & BOOTY
LEGS_BOOTY_L2_SATURDAY = [
    {"name": "Squat", "sets": "1 warm up + 3", "reps": "10-12", "category": "Legs"},
    {"name": "Leg Press", "sets": "3", "reps": "12-15", "category": "Legs"},
    {"name": "Bulgarian Split Squats", "sets": "3 each leg", "reps": "10-12", "category": "Legs"},
    {"name": "Leg Curls", "sets": "3", "reps": "10-12", "category": "Legs"},
    {"name": "Cable Kickbacks", "sets": "3 each leg", "reps": "12-15", "category": "Booty"},
    {"name": "Walking Lunges", "sets": "3", "reps": "20 total", "category": "Legs"}
]
# ============================================================================
# MEAL PLAN DATA
# ============================================================================
WEEKLY_MEALS = {
    "Option A: Omnivore": {
        "Monday": ["Greek yogurt + berries + oats", "Chicken, rice & broccoli", "Salmon, sweet potato, asparagus"],
        "Tuesday": ["Omelet + toast + fruit", "Turkey wrap + mixed greens", "Beef stir-fry + jasmine rice"],
        "Wednesday": ["Protein smoothie + banana + PB", "Chicken fajita bowl", "Shrimp tacos + slaw"],
        "Thursday": ["Overnight oats + chia + berries", "Sushi bowl (salmon, rice, edamame)",
                     "Lean beef chili + quinoa"],
        "Friday": ["Eggs + avocado toast", "Grilled chicken Caesar", "Baked cod + potatoes + green beans"],
        "Saturday": ["Protein pancakes + fruit", "Turkey burger + salad", "Steak + rice + vegetables"],
        "Sunday": ["Cottage cheese + pineapple + granola", "Chicken pesto pasta + veggies",
                   "Roast chicken + couscous + salad"]
    },
    "Option B: Pescatarian": {
        "Monday": ["Greek yogurt + berries + oats", "Tuna salad wrap + greens", "Salmon, sweet potato, asparagus"],
        "Tuesday": ["Tofu scramble + toast", "Shrimp quinoa bowl", "Baked cod + potatoes + broccoli"],
        "Wednesday": ["Protein smoothie + banana", "Sushi bowl", "Garlic shrimp pasta + salad"],
        "Thursday": ["Overnight oats + chia", "Miso salmon + rice + bok choy", "Veggie chili + avocado toast"],
        "Friday": ["Eggs + avocado toast", "Mediterranean tuna pasta", "Seared tuna + rice + edamame"],
        "Saturday": ["Protein pancakes + fruit", "Grilled shrimp tacos + slaw", "Baked halibut + quinoa + veg"],
        "Sunday": ["Cottage cheese + fruit", "Smoked salmon bagel", "Shrimp stir-fry + brown rice"]
    },
    "Option C: Vegan": {
        "Monday": ["Tofu scramble + toast + fruit", "Lentil quinoa bowl + veggies", "Tempeh stir-fry + rice"],
        "Tuesday": ["Overnight oats + chia + berries", "Chickpea wrap + greens", "Black bean pasta + broccoli"],
        "Wednesday": ["Pea-protein smoothie + banana + PB", "Buddha bowl", "Lentil curry + basmati rice"],
        "Thursday": ["Buckwheat pancakes + fruit", "Hummus + falafel bowl", "Tofu poke bowl"],
        "Friday": ["Tofu scramble burrito", "Pea-protein pasta + marinara", "Tempeh fajitas + tortillas"],
        "Saturday": ["Oatmeal + seeds + berries", "Chickpea quinoa bowl", "Tofu steak + potatoes + veg"],
        "Sunday": ["Soy yogurt + granola + fruit", "Vegan sushi + edamame", "Lentil bolognese + pasta"]
    }
}


# ============================================================================
# PAGE COMPONENTS
# ============================================================================
def render_hero():
    """Render the hero section"""
    st.markdown("""
    <div class="hero-section">
        <h1 class="main-header">HOURGLASS FITNESS TRANSFORMATION</h1>
        <p class="sub-header">12-Week plan for Booty, Core, Back & Shoulders — by Joane Aristilde</p>
    </div>
    """, unsafe_allow_html=True)


def render_homepage():
    """Render the main homepage - ENHANCED"""
    render_hero()

    # NEW: Personalization card at top
    render_personalization_card()

    st.markdown(f"## 🏠 {i18n('welcome')}")

    # Admin photo upload section
    if ADMIN_UI:
        with st.expander("🔧 Admin: Upload Coach Photo"):
            uploaded_photo = st.file_uploader(
                "Choose your photo to display on the homepage",
                type=['jpg', 'jpeg', 'png'],
                key="homepage_coach_photo"
            )
            if uploaded_photo is not None:
                # Save the uploaded photo
                try:
                    with open("coach_photo.jpg", "wb") as f:
                        f.write(uploaded_photo.getbuffer())
                    st.success("Photo saved! It will appear below.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error saving photo: {str(e)}")

    # Display coach photo - smaller and better positioned
    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        if os.path.exists("coach_photo.jpg"):
            st.image("coach_photo.jpg", caption="Hourglass Fitness", width=450)
        elif ADMIN_UI:
            st.info("👆 Use the admin panel above to upload your photo")

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div class="info-card">
            <h3>✨ Transform Your Body</h3>
            <p>This comprehensive 12-week program is designed specifically for building your booty,
            strengthening your core, and sculpting your back and shoulders.</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="info-card">
            <h3>🎯 Your Goals, Your Way</h3>
            <p>Choose between Level 1 (beginner-friendly) or Level 2 (advanced) workouts.
            Track your progress, follow meal plans, and achieve lasting results!</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("## 🚀 Quick Navigation")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("📚 Workout Overview", use_container_width=True, type="primary"):
            st.session_state.page = "workout_overview"
            st.rerun()

    with col2:
        if st.button("💪 Today's Workout", use_container_width=True, type="primary"):
            st.session_state.page = "workout_tracker"
            st.rerun()

    with col3:
        if st.button("🍽️ Meal Plans", use_container_width=True, type="primary"):
            st.session_state.page = "meal_plans"
            st.rerun()

    with col4:
        if st.button("📊 Weight Tracker", use_container_width=True, type="primary"):
            st.session_state.page = "weight_tracker"
            st.rerun()

    st.markdown("---")

    # Getting Started Tabs
    st.markdown("### 🎓 Getting Started")

    tab_guide, tab_video = st.tabs(["📖 How to Use This App", "🎥 Getting Started Video"])

    with tab_guide:
        with st.expander("How to Use This App", expanded=True):
            st.markdown("""
            1. **Read the Workout Overview** - Understand the program structure and principles
            2. **Choose Your Level** - Start with Level 1 if you're new to this program
            3. **Follow Daily Workouts** - Use the workout tracker to log your exercises
            4. **Track Your Progress** - Use the weight tracker to monitor your transformation
            5. **Follow Meal Plans** - Nutrition is key to your success!

            **Remember:** Consistency and proper form are the keys to success! 💪
            """)

    with tab_video:
        st.markdown("#### 'Getting Started' Video")
        videos = load_videos_json()
        src = videos.get("__getting_started__")

        # Viewer: always allowed to watch
        if src:
            try:
                _, col_vid_gs, _ = st.columns([1, 2, 1])
                with col_vid_gs:
                    if src.startswith(("http", "https")):
                        st.video(src)
                    elif os.path.exists(src):
                        st.video(src)
                    else:
                        st.warning("Saved video file not found. It may have been moved or deleted.")
            except Exception as e:
                st.error(f"Could not display video: {e}")
        else:
            st.info("No 'Getting Started' video has been saved yet.")

        # Admin-only controls
        if ADMIN_UI:
            with st.expander("🔧 Admin: Set / Change 'Getting Started' Video", expanded=False):
                uploaded_file = st.file_uploader(
                    "Upload a video file",
                    type=["mp4", "mov", "m4v"],
                    key="getting_started_uploader"
                )
                video_url = st.text_input(
                    "Or, provide a video URL",
                    placeholder="https://www.youtube.com/watch?v=...",
                    key="getting_started_url"
                )

                c1, c2 = st.columns(2)
                with c1:
                    if st.button("Save Video", key="save_getting_started", type="primary"):
                        source_to_save = None
                        if uploaded_file is not None:
                            try:
                                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                safe_filename = re.sub(r'[^a-zA-Z0-9._-]', '', uploaded_file.name)
                                filename = f"getting_started_{timestamp}_{safe_filename}"
                                video_path = os.path.join(VIDEOS_DIR, filename)

                                with open(video_path, "wb") as f:
                                    f.write(uploaded_file.getbuffer())
                                source_to_save = video_path
                                st.success(f"File '{uploaded_file.name}' uploaded successfully!")
                            except Exception as e:
                                st.error(f"Failed to save uploaded file: {e}")
                        elif video_url:
                            source_to_save = video_url
                            st.success("Video URL saved!")
                        else:
                            st.warning("Please upload a file or provide a URL to save.")

                        if source_to_save:
                            videos["__getting_started__"] = source_to_save
                            if save_videos_json(videos):
                                st.rerun()
                with c2:
                    if src and st.button("Delete Video", key="delete_getting_started"):
                        if "__getting_started__" in videos:
                            del videos["__getting_started__"]
                            if save_videos_json(videos):
                                st.success("Deleted 'Getting Started' video.")
                                st.rerun()

    # Quick stats if user has data
    if st.session_state.get('progress_entries') or st.session_state.get('completed_exercises'):
        st.markdown("### 📈 Your Quick Stats")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Current Level", f"Level {st.session_state.selected_level}")

        with col2:
            completed = len([e for e in st.session_state.completed_exercises if e])
            st.metric("Exercises Completed", completed)

        with col3:
            entries = len(st.session_state.get('progress_entries', []))
            st.metric("Progress Entries", entries)

    # Add intro video at bottom
    render_homepage_intro_video()


def render_workout_overview():
    """Render the workout overview page"""
    st.markdown("# 📚 Workout Overview")

    tab1, tab2, tab3, tab4 = st.tabs(
        ["Program Structure", "Progressive Overload", "Exercise Guide", "About Your Coach"])

    with tab1:
        st.markdown("""
        ## Your Workout Journey Starts Here! 💪

        ### How Your Plan Works
        Ready to get stronger? Your workouts are split into easy-to-follow categories:
        - **Booty** — Shape and strengthen your glutes
        - **Legs & Booty** — Power up your lower body
        - **Light Shoulders & Back** — Build upper body strength
        - **Abs/Core Only** — Perfect for home workouts

        ### Pick Your Starting Point
        - **New to fitness?** Start with **Level 1** to build confidence.
        - **Ready for more?** Move to **Level 2** when Level 1 feels easy.

        ### Bonus Workouts
        On a rest day and feel motivated? Try **Abs/Core Only** (great at home).

        > **Important:** Listen to your body. Rest days are when muscles grow stronger.

        ### Pro Tips for Success
        ✨ **Level 2** is the exact workout I use personally.
        ✨ I switch routines every **12 weeks** to keep things fresh and challenging.
        ✨ Follow the **exercise order**—it's structured for best results.

        **Remember:** Every rep gets you stronger. Every workout gets you closer to your goals.
        """)

        # Show weekly schedules
        st.markdown("---")
        st.markdown("### 📅 Weekly Schedules")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Level 1")
            schedule_df = pd.DataFrame(list(PROGRAM_SPLIT["Level 1"].items()), columns=["Day", "Workout"])
            st.table(schedule_df)

        with col2:
            st.markdown("#### Level 2")
            schedule_df = pd.DataFrame(list(PROGRAM_SPLIT["Level 2"].items()), columns=["Day", "Workout"])
            st.table(schedule_df)

    with tab2:
        st.markdown("""
        ## 🚀 Progressive Overload: The Key to Growth

        ### What Is Progressive Overload?
        Progressive overload is gradually increasing the demands on your muscles to force them to adapt and grow stronger.

        ### How to Apply It:

        **Week 1-2: Foundation**
        - Focus on form and technique
        - Use lighter weights to learn movements
        - Track your starting weights

        **Week 3-4: Building**
        - Increase weight by 5-10% when you can complete all sets
        - Maintain proper form
        - Add 1-2 reps if weight increase is too much

        **Week 5-8: Progressing**
        - Continue increasing weight gradually
        - Focus on mind-muscle connection
        - Consider adding pause reps or tempo work

        **Week 9-12: Pushing**
        - Challenge yourself with heavier weights
        - Add intensity techniques (drop sets, supersets)
        - Prepare for next program cycle

        ### Progressive Overload Methods:
        1. **Increase Weight** - Add 2.5-5 lbs when ready
        2. **Add Reps** - Go from 10 to 12 reps before increasing weight
        3. **Add Sets** - Progress from 3 to 4 sets
        4. **Decrease Rest** - Reduce rest between sets
        5. **Improve Form** - Better technique = more muscle activation

        ### When to Progress:
        - ✅ You complete all sets and reps with good form
        - ✅ The last 2-3 reps feel challenging but doable
        - ✅ You've done the same weight for 2-3 workouts

        ### Safety First:
        - ⚠️ Never sacrifice form for heavier weight
        - ⚠️ Listen to your body - some days you need to maintain or reduce
        - ⚠️ Proper warm-up is essential before heavy lifts
        """)

    with tab3:
        st.markdown("""
        ## 📖 Exercise Guide

        ### Key Exercise Categories:

        **🍑 Booty Builders**
        - Hip Thrusts: The #1 glute builder
        - RDLs: Target glutes and hamstrings
        - Kickbacks: Isolation for glute activation
        - Hyperextensions: Posterior chain development

        **🦵 Leg Shapers**
        - Bulgarian Split Squats: Unilateral strength
        - Leg Press: Quad and glute development
        - Leg Curls: Hamstring isolation

        **💪 Upper Body**
        - Lat Pulldowns: Back width
        - Rows: Back thickness
        - Shoulder Press: Deltoid development
        - Face Pulls: Rear delts and posture

        **🎯 Core**
        - Planks: Core stability
        - Dead Bugs: Core control
        - Leg Raises: Lower abs

        ### Form Tips:
        - Always warm up before working sets
        - Control the eccentric (lowering) phase
        - Focus on mind-muscle connection
        - Full range of motion > heavy weight
        """)

    with tab4:
        st.markdown("""
        ## 👩‍🏫 About Your Coach - Joane Aristilde
        """)

        col1, col2 = st.columns([1, 2])

        with col1:
            # Check for coach photo
            coach_photo_path = "coach_photo.jpg"
            if os.path.exists(coach_photo_path):
                st.image(coach_photo_path, caption="Joane Aristilde", width=250)
            elif ADMIN_UI:
                st.info("Upload coach_photo.jpg to display photo")
                with st.expander("🔧 Admin: Upload Coach Photo"):
                    uploaded_photo = st.file_uploader("Upload Coach Photo", type=['jpg', 'jpeg', 'png'],
                                                      key="coach_photo_upload_overview")
                    if uploaded_photo:
                        with open("coach_photo.jpg", "wb") as f:
                            f.write(uploaded_photo.getbuffer())
                        st.success("Photo uploaded! Refresh to see it.")
                        st.rerun()

        with col2:
            st.markdown("""
            ### Your Transformation Partner

            Welcome! I'm Joane Aristilde, and I'm here to guide you through your fitness transformation journey.

            **My Philosophy:**
            - Building strength builds confidence
            - Consistency beats perfection
            - Your body is capable of amazing things
            - Every workout is a step toward your goals

            **This Program Features:**
            - ✅ 12 weeks of structured workouts
            - ✅ Progressive overload for real results
            - ✅ Focus on glutes, core, and upper body
            - ✅ Suitable for gym or home modifications
            - ✅ Nutrition guidance included

            **My Promise to You:**
            Follow this program, stay consistent, and you WILL see results.
            I've designed every workout with your success in mind.

            Let's build your dream body together! 💪
            """)

        st.markdown("---")
        st.info("💡 **Pro Tip:** Take progress photos every week to see your amazing transformation!")


def render_workout_tracker():
    """Render the workout tracker page - ENHANCED"""
    st.markdown("# 💪 Workout Tracker")

    # Show admin mode status
    if ADMIN_UI:
        st.success("🔧 **Admin Mode Active** - You can upload/manage videos directly in each exercise")

    # Admin panel at top if in admin mode (for managing all videos at once)
    if ADMIN_UI:
        render_admin_video_manager()

    # Level selection
    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        if st.button("🌟 Level 1", use_container_width=True):
            st.session_state.selected_level = 1
            st.session_state.selected_workout = None
            st.rerun()

    with col2:
        if st.button("🔥 Level 2", use_container_width=True):
            st.session_state.selected_level = 2
            st.session_state.selected_workout = None
            st.rerun()

    with col3:
        st.info(f"**Current: Level {st.session_state.selected_level}**")

    # Today's workout
    today = date.today().strftime("%A")
    schedule = PROGRAM_SPLIT[f"Level {st.session_state.selected_level}"]

    st.markdown("---")

    # Workout selection
    st.markdown("### 📅 Select Your Workout")

    # Weekly view
    cols = st.columns(7)
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    for idx, (col, day) in enumerate(zip(cols, days)):
        with col:
            workout = schedule[day]
            is_today = day == today

            if is_today:
                st.markdown(f"**📍 {day}**")
            else:
                st.markdown(f"{day}")

            if workout == "REST":
                st.markdown("🛋️ *Rest*")
            else:
                if st.button(
                        workout,
                        key=f"day_{day}",
                        use_container_width=True,
                        type="primary" if is_today else "secondary"
                ):
                    st.session_state.selected_workout = workout
                    st.session_state.selected_workout_day = day
                    st.rerun()

    st.markdown("---")

    # Display selected workout
    if st.session_state.selected_workout:
        workout_label = st.session_state.selected_workout
        workout_day = st.session_state.selected_workout_day
        workout_date = date.today().isoformat()

        st.markdown(f"## 🎯 {workout_day}: {workout_label}")

        # Get exercises for this workout
        exercises = get_exercises_for_day(
            st.session_state.selected_level,
            workout_day,
            workout_label
        )

        # Display enhanced exercise cards with video and tracking
        for idx, exercise in enumerate(exercises, 1):
            render_enhanced_exercise_card(exercise, idx, workout_date)
            st.markdown("---")
    else:
        st.info("👆 Select a workout day above to see exercises")


def get_exercises_for_day(level, day_name, workout_label):
    """Get exercises for a specific day and workout"""
    # Handle REST days
    if workout_label == "REST":
        return [{"name": "Rest Day", "sets": "—", "reps": "Recovery", "category": "Rest"}]

    # Level 1 workouts
    if level == 1:
        if day_name == "Monday" and "BOOTY" in workout_label:
            return BOOTY_L1_MONDAY
        elif day_name == "Tuesday" and "SHOULDERS" in workout_label:
            return SHOULDERS_BACK_LIGHT
        elif day_name == "Wednesday" and "CARDIO" in workout_label:
            return CARDIO_WEDNESDAY
        elif day_name == "Thursday" and "LEGS" in workout_label:
            return LEGS_BOOTY_L1_THURSDAY
        elif day_name == "Friday" and "SHOULDERS" in workout_label:
            return SHOULDERS_ABS_FRIDAY
        elif day_name == "Saturday" and "SHOULDERS" in workout_label:
            return SHOULDERS_BACK_LIGHT  # Saturday repeats Tuesday for Level 1
        elif "ABS/CORE" in workout_label:
            return ABS_CORE_ONLY

    # Level 2 workouts
    elif level == 2:
        if day_name == "Monday" and "BOOTY" in workout_label:
            return BOOTY_L2_MONDAY
        elif day_name == "Tuesday" and "SHOULDERS" in workout_label:
            return SHOULDERS_BACK_LIGHT
        elif day_name == "Wednesday" and "CARDIO" in workout_label:
            return CARDIO_WEDNESDAY
        elif day_name == "Thursday" and "BOOTY" in workout_label:
            return BOOTY_L2_THURSDAY  # This will now use your new workout
        elif day_name == "Friday" and "SHOULDERS" in workout_label:
            return SHOULDERS_ABS_FRIDAY
        elif day_name == "Saturday" and "LEGS" in workout_label:
            return LEGS_BOOTY_L2_SATURDAY
        elif "ABS/CORE" in workout_label:
            return ABS_CORE_ONLY

    # Default fallback
    return [
        {"name": "Exercise 1", "sets": "3", "reps": "10-12", "category": "Main"},
        {"name": "Exercise 2", "sets": "3", "reps": "10-12", "category": "Main"},
        {"name": "Exercise 3", "sets": "3", "reps": "10-12", "category": "Accessory"},
    ]


def render_exercise_card(exercise, idx):
    """Render a single exercise card - ORIGINAL (kept for compatibility)"""
    with st.container():
        col1, col2 = st.columns([3, 1])

        with col1:
            st.markdown(f"### {idx}. {exercise['name']}")
            st.markdown(f"**Sets:** {exercise['sets']} | **Reps:** {exercise['reps']}")
            st.markdown(f"*Category: {exercise['category']}*")

        with col2:
            # Simple checkbox for completion
            key = f"ex_{idx}_{exercise['name'].replace(' ', '_')}"
            completed = st.checkbox("✅ Done", key=key)

            if completed and key not in st.session_state.completed_exercises:
                st.session_state.completed_exercises.append(key)


def render_meal_plans():
    """Render the meal plans page"""
    st.markdown("# 🍽️ Meal Plans")

    tab1, tab2, tab3 = st.tabs(["Weekly Plans", "Macro Calculator", "Nutrition Tips"])

    with tab1:
        st.markdown("## 📅 Weekly Meal Plans")

        # Diet type selection
        diet_type = st.selectbox(
            "Select your diet type:",
            list(WEEKLY_MEALS.keys()),
            key="meal_plan_selector"
        )

        # Display meal plan
        meals = WEEKLY_MEALS[diet_type]

        # Create a properly formatted dataframe
        meal_data = []
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

        for day in days:
            if day in meals:
                meal_data.append({
                    "Day": day,
                    "Breakfast": meals[day][0] if len(meals[day]) > 0 else "",
                    "Lunch": meals[day][1] if len(meals[day]) > 1 else "",
                    "Dinner": meals[day][2] if len(meals[day]) > 2 else ""
                })

        df = pd.DataFrame(meal_data)
        st.table(df)

        # Nutrition tips
        with st.expander("💡 Nutrition Tips"):
            st.markdown("""
            ### Key Points for Success:
            - **Protein Priority:** Aim for 0.8-1g per pound of body weight
            - **Hydration:** Drink at least 2-3L of water daily
            - **Meal Timing:** Eat protein within 2 hours post-workout
            - **Consistency:** Stick to your plan 80% of the time
            - **Flexibility:** Allow for treats and social occasions

            ### For Muscle Growth:
            - Slight caloric surplus (200-300 calories above maintenance)
            - Focus on whole foods
            - Don't skip carbs - they fuel your workouts!
            - Consider creatine supplementation (5g daily)
            """)

    with tab2:
        st.markdown("## 🧮 Macro Calculator")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### Your Stats")
            weight = st.number_input("Weight (lbs)", 100, 300, 150)
            height = st.number_input("Height (inches)", 50, 80, 65)
            age = st.number_input("Age", 18, 80, 25)
            activity = st.selectbox(
                "Activity Level",
                ["Sedentary", "Lightly Active", "Moderately Active", "Very Active"]
            )

        with col2:
            st.markdown("### Your Goals")
            goal = st.selectbox("Goal", ["Lose Fat", "Maintain", "Build Muscle"])

            # Simple calorie calculation
            if activity == "Sedentary":
                multiplier = 1.2
            elif activity == "Lightly Active":
                multiplier = 1.375
            elif activity == "Moderately Active":
                multiplier = 1.55
            else:
                multiplier = 1.725

            # Basic BMR calculation (Mifflin-St Jeor)
            bmr = (10 * weight * 0.453592) + (6.25 * height * 2.54) - (5 * age) - 161
            tdee = bmr * multiplier

            if goal == "Lose Fat":
                calories = tdee - 300
            elif goal == "Maintain":
                calories = tdee
            else:  # Build Muscle
                calories = tdee + 300

            st.markdown("### Your Daily Targets")
            st.metric("Calories", f"{int(calories)} kcal")

            # Macro split
            protein_g = int(weight * 0.8)
            fat_g = int(calories * 0.25 / 9)
            carbs_g = int((calories - (protein_g * 4) - (fat_g * 9)) / 4)

            col_a, col_b, col_c = st.columns(3)
            col_a.metric("Protein", f"{protein_g}g")
            col_b.metric("Carbs", f"{carbs_g}g")
            col_c.metric("Fat", f"{fat_g}g")

    with tab3:
        st.markdown("""
        ## 🥗 Nutrition Tips for Success

        ### Pre-Workout (30-60 min before)
        - Banana + peanut butter
        - Rice cakes + honey
        - Oatmeal + berries
        - Coffee or green tea

        ### Post-Workout (within 2 hours)
        - Protein shake + fruit
        - Greek yogurt + granola
        - Chicken + rice
        - Tuna sandwich

        ### Supplements to Consider
        - **Creatine:** 5g daily for strength and muscle
        - **Protein Powder:** Convenient protein source
        - **Multivitamin:** Cover nutritional gaps
        - **Omega-3:** Anti-inflammatory benefits
        - **Vitamin D:** Especially if limited sun exposure

        ### Hydration Goals
        - Minimum: 2-3 liters per day
        - During workout: 500-750ml
        - Add electrolytes for intense sessions

        ### 80/20 Rule
        Eat nutritious whole foods 80% of the time, enjoy treats 20% of the time!
        """)


def render_weight_tracker():
    """Render the weight tracker page"""
    st.markdown("# 📊 Weight Tracker")

    # Initialize weight tracker storage if available
    if STORAGE_AVAILABLE:
        init_storage()

    tab1, tab2, tab3 = st.tabs(["Daily Entry", "Progress Charts", "History"])

    with tab1:
        st.markdown("## 📝 Daily Check-in")

        with st.form("daily_weight_entry"):
            col1, col2, col3 = st.columns(3)

            with col1:
                weight = st.number_input("Weight (lbs)", 80.0, 400.0, 150.0, 0.5)
                waist = st.number_input("Waist (inches)", 20.0, 60.0, 30.0, 0.5)
                hips = st.number_input("Hips (inches)", 25.0, 70.0, 36.0, 0.5)

            with col2:
                water = st.number_input("Water (liters)", 0.0, 10.0, 2.5, 0.25)
                calories_in = st.number_input("Calories In", 0, 5000, 1700, 50)
                calories_out = st.number_input("Calories Out", 0, 2000, 400, 50)

            with col3:
                energy = st.slider("Energy Level", 1, 10, 7)
                sleep = st.number_input("Sleep (hours)", 0.0, 12.0, 7.0, 0.5)

            notes = st.text_area("Notes", placeholder="How are you feeling? Any observations?")

            submitted = st.form_submit_button("💾 Save Entry", use_container_width=True, type="primary")

            if submitted:
                try:
                    # Save to session state
                    entry = {
                        "date": date.today().isoformat(),
                        "weight": weight,
                        "waist": waist,
                        "hips": hips,
                        "water": water,
                        "calories_in": calories_in,
                        "calories_out": calories_out,
                        "net_calories": calories_in - calories_out,
                        "energy": energy,
                        "sleep": sleep,
                        "notes": notes
                    }

                    if "weight_entries" not in st.session_state:
                        st.session_state.weight_entries = []

                    st.session_state.weight_entries.append(entry)

                    # Save user progress
                    save_user_progress()

                    # Also save using storage module if available
                    if STORAGE_AVAILABLE:
                        try:
                            save_daily_log(
                                user_id="default",
                                date=date.today().isoformat(),
                                weight_kg=weight * 0.453592,
                                water_l=water,
                                cal_in=calories_in,
                                cal_out=calories_out,
                                waist_in=waist,
                                hips_in=hips,
                                energy_1_10=energy,
                                notes=notes,
                                photo_path=None,
                                on_target_flag="OK"
                            )
                        except:
                            pass  # Storage module might not be working

                    st.success("✅ Entry saved successfully!")
                    st.balloons()
                    st.rerun()

                except Exception as e:
                    st.error(f"Error saving entry: {str(e)}")

    with tab2:
        st.markdown("## 📈 Progress Charts")

        if st.session_state.get("weight_entries"):
            # Convert to DataFrame
            df = pd.DataFrame(st.session_state.weight_entries)
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')

            # Weight trend
            st.markdown("### Weight Trend")
            weight_data = df[['date', 'weight']].dropna()
            if not weight_data.empty:
                st.line_chart(weight_data.set_index('date')['weight'])

            # Metrics
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                if len(df) >= 2:
                    weight_change = df.iloc[-1]['weight'] - df.iloc[0]['weight']
                    st.metric("Weight Change", f"{weight_change:+.1f} lbs")
                else:
                    st.metric("Weight Change", "N/A")

            with col2:
                avg_calories = df['net_calories'].mean() if 'net_calories' in df else 0
                st.metric("Avg Net Calories", f"{int(avg_calories)}")

            with col3:
                avg_water = df['water'].mean() if 'water' in df else 0
                st.metric("Avg Water", f"{avg_water:.1f}L")

            with col4:
                avg_energy = df['energy'].mean() if 'energy' in df else 0
                st.metric("Avg Energy", f"{avg_energy:.1f}/10")

            # Waist to Hip Ratio
            if 'waist' in df.columns and 'hips' in df.columns:
                st.markdown("### Waist-to-Hip Ratio")
                df['wh_ratio'] = df['waist'] / df['hips']
                ratio_data = df[['date', 'wh_ratio']].dropna()
                if not ratio_data.empty:
                    st.line_chart(ratio_data.set_index('date')['wh_ratio'])
        else:
            st.info("📊 Start tracking to see your progress charts!")

    with tab3:
        st.markdown("## 📜 History")

        if st.session_state.get("weight_entries"):
            df = pd.DataFrame(st.session_state.weight_entries)
            df = df.sort_values('date', ascending=False)

            # Display table with formatted columns
            display_df = df[
                ['date', 'weight', 'waist', 'hips', 'water', 'calories_in', 'calories_out', 'energy', 'sleep']].copy()
            display_df['date'] = pd.to_datetime(display_df['date']).dt.strftime('%Y-%m-%d')

            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True
            )

            # Export option
            if st.button("📥 Export to CSV", use_container_width=True):
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"weight_tracker_{date.today()}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
        else:
            st.info("📝 No entries yet. Start tracking above!")


def sidebar_navigation():
    """Sidebar navigation - ENHANCED"""
    with st.sidebar:
        st.markdown("# 🏋️ Navigation")
        st.caption(f"Admin UI: {'ON' if ADMIN_UI else 'OFF'} • Read-only: {'ON' if READ_ONLY else 'OFF'}")

        # Navigation buttons
        pages = {
            "home": "🏠 Home",
            "workout_overview": "📚 Workout Overview",
            "workout_tracker": "💪 Workout Tracker",
            "meal_plans": "🍽️ Meal Plans",
            "weight_tracker": "📊 Weight Tracker",
            "coach_jo": "🤖 Coach Jo",
            "streaks": "⭐ Streaks & Badges",
            "community": "👥 Community",
            "devices": "🔗 Devices"
        }

        for page_key, page_name in pages.items():
            if st.button(
                    page_name,
                    key=f"nav_{page_key}",
                    use_container_width=True,
                    type="primary" if st.session_state.page == page_key else "secondary"
            ):
                st.session_state.page = page_key
                st.rerun()

        st.markdown("---")

        # Quick Stats
        st.markdown("### 📈 Quick Stats")
        st.metric("Current Level", f"Level {st.session_state.selected_level}")

        completed = len(st.session_state.completed_exercises)
        st.metric("Exercises Done", completed)

        if st.session_state.get("weight_entries"):
            entries = len(st.session_state.weight_entries)
            st.metric("Weight Entries", entries)

        # Show admin mode indicator
        if ADMIN_UI:
            st.markdown("---")
            st.success("🔧 Admin Mode Active")

        st.markdown("---")

        # NEW: Accessibility settings
        render_accessibility_settings()

        # Settings
        with st.expander("⚙️ Settings"):
            if st.button("🔄 Reset All Data", use_container_width=True):
                if st.checkbox("Confirm reset"):
                    for key in ["completed_exercises", "progress_entries", "weight_entries", "workout_sets",
                                "coach_history", "community_chat"]:
                        if key in st.session_state:
                            st.session_state[key] = [] if key != "workout_sets" else {}
                    # Reset user progress
                    st.session_state.prefs = {
                        "experience": "beginner",
                        "focus": ["glutes", "core"],
                        "equipment": ["dumbbells", "machines", "bodyweight"]
                    }
                    st.session_state.ai_tuning = {
                        "injury_notes": "",
                        "available_days": 4,
                        "diet": "omnivore",
                        "protein_target_g": 120
                    }
                    save_user_progress()
                    st.success("Data reset!")
                    st.rerun()


# ============================================================================
# MAIN APP
# ============================================================================
def main():
    """Main application"""
    # Initialize
    init_session_state()
    load_styles()

    # Apply accessibility CSS
    apply_accessibility_css()

    # Sidebar
    sidebar_navigation()

    # Route to appropriate page
    page = st.session_state.get("page", "home")

    if page == "home":
        render_homepage()
    elif page == "workout_overview":
        render_workout_overview()
    elif page == "workout_tracker":
        render_workout_tracker()
    elif page == "meal_plans":
        render_meal_plans()
    elif page == "weight_tracker":
        render_weight_tracker()
    elif page == "coach_jo":
        render_coach_jo_tab()
    elif page == "streaks":
        render_streaks_tab()
    elif page == "community":
        render_community_tab()
    elif page == "devices":
        render_devices_tab()
    else:
        render_homepage()


if __name__ == "__main__":
    main()