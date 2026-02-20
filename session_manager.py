"""
Session management for the AI2Thor Dataset Viewer quiz.
Handles saving/loading quiz progress, bookmarks, and session history.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

# Session directory
SESSIONS_DIR = Path("./sessions")
CURRENT_SESSION_FILE = SESSIONS_DIR / "current_session.json"


def ensure_sessions_dir():
    """Create sessions directory if it doesn't exist."""
    SESSIONS_DIR.mkdir(exist_ok=True)


def create_empty_session(dataset: str, split_subset: str) -> Dict[str, Any]:
    """Create a new empty session."""
    return {
        "id": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "dataset": dataset,
        "split_subset": split_subset,
        "total_questions": 0,
        "answered_count": 0,
        "correct_count": 0,
        "incorrect_count": 0,
        "answers": {},  # row_idx -> {question, user_answer, correct_answer, is_correct, timestamp}
        "bookmarks": [],  # list of row indices
        "current_row": 0,
    }


def load_current_session() -> Optional[Dict[str, Any]]:
    """Load the current session from file."""
    ensure_sessions_dir()
    if CURRENT_SESSION_FILE.exists():
        try:
            with open(CURRENT_SESSION_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None
    return None


def save_current_session(session: Dict[str, Any]):
    """Save the current session to file."""
    ensure_sessions_dir()
    session["updated_at"] = datetime.now().isoformat()
    with open(CURRENT_SESSION_FILE, "w") as f:
        json.dump(session, f, indent=2)


def archive_session(session: Dict[str, Any]) -> str:
    """Archive the current session to a timestamped file."""
    ensure_sessions_dir()
    session["archived_at"] = datetime.now().isoformat()

    # Create filename with session ID
    filename = f"session_{session['id']}.json"
    filepath = SESSIONS_DIR / filename

    with open(filepath, "w") as f:
        json.dump(session, f, indent=2)

    return str(filepath)


def record_answer(
    session: Dict[str, Any],
    row_idx: int,
    question: str,
    user_answer: str,
    correct_answer: str,
    is_correct: bool,
    query_object: str = ""
) -> Dict[str, Any]:
    """Record an answer in the session (first time only)."""
    row_key = str(row_idx)

    # Only record if not already answered
    if row_key not in session["answers"]:
        session["answers"][row_key] = {
            "question": question,
            "user_answer": user_answer,
            "correct_answer": correct_answer,
            "is_correct": is_correct,
            "query_object": query_object,
            "timestamp": datetime.now().isoformat()
        }
        session["answered_count"] = len(session["answers"])
        if is_correct:
            session["correct_count"] += 1
        else:
            session["incorrect_count"] += 1

        save_current_session(session)

    return session


def record_answer_allow_change(
    session: Dict[str, Any],
    row_idx: int,
    question: str,
    user_answer: str,
    correct_answer: str,
    is_correct: bool,
    query_object: str = "",
    was_answered: bool = False,
    previous_correct: bool = False
) -> Dict[str, Any]:
    """Record or update an answer in the session, allowing answer changes."""
    row_key = str(row_idx)

    # Initialize answers dict if not present (backward compatibility)
    if "answers" not in session:
        session["answers"] = {}

    # Initialize counts if not present (backward compatibility)
    if "answered_count" not in session:
        session["answered_count"] = len(session.get("answers", {}))
    if "correct_count" not in session:
        session["correct_count"] = sum(1 for a in session.get("answers", {}).values() if a.get("is_correct"))
    if "incorrect_count" not in session:
        session["incorrect_count"] = sum(1 for a in session.get("answers", {}).values() if not a.get("is_correct"))

    # If changing an existing answer, adjust counts
    if was_answered:
        # Remove old count
        if previous_correct:
            session["correct_count"] = max(0, session.get("correct_count", 0) - 1)
        else:
            session["incorrect_count"] = max(0, session.get("incorrect_count", 0) - 1)

    # Record/update the answer
    session["answers"][row_key] = {
        "question": question,
        "user_answer": user_answer,
        "correct_answer": correct_answer,
        "is_correct": is_correct,
        "query_object": query_object,
        "timestamp": datetime.now().isoformat()
    }

    # Update counts
    session["answered_count"] = len(session["answers"])
    if is_correct:
        session["correct_count"] = session.get("correct_count", 0) + 1
    else:
        session["incorrect_count"] = session.get("incorrect_count", 0) + 1

    save_current_session(session)
    return session


def toggle_bookmark(session: Dict[str, Any], row_idx: int) -> Dict[str, Any]:
    """Toggle bookmark for a row."""
    if row_idx in session["bookmarks"]:
        session["bookmarks"].remove(row_idx)
    else:
        session["bookmarks"].append(row_idx)

    save_current_session(session)
    return session


def is_row_answered(session: Dict[str, Any], row_idx: int) -> bool:
    """Check if a row has been answered."""
    return str(row_idx) in session["answers"]


def is_row_bookmarked(session: Dict[str, Any], row_idx: int) -> bool:
    """Check if a row is bookmarked."""
    return row_idx in session["bookmarks"]


def get_next_unanswered_row(session: Dict[str, Any], current_idx: int, total_rows: int, direction: int = 1) -> int:
    """Find the next unanswered row in the given direction."""
    checked = 0
    idx = current_idx

    while checked < total_rows:
        idx = (idx + direction) % total_rows
        if not is_row_answered(session, idx):
            return idx
        checked += 1

    # All rows answered, return current
    return current_idx


def get_session_stats(session: Dict[str, Any]) -> Dict[str, Any]:
    """Get session statistics."""
    total = session.get("total_questions", 0)
    answered = session.get("answered_count", 0)
    correct = session.get("correct_count", 0)
    incorrect = session.get("incorrect_count", 0)

    return {
        "total": total,
        "answered": answered,
        "remaining": total - answered,
        "correct": correct,
        "incorrect": incorrect,
        "accuracy": (correct / answered * 100) if answered > 0 else 0,
        "progress": (answered / total * 100) if total > 0 else 0,
        "bookmarks": len(session.get("bookmarks", []))
    }


def list_archived_sessions() -> List[Dict[str, Any]]:
    """List all archived sessions with basic info."""
    ensure_sessions_dir()
    sessions = []

    for filepath in SESSIONS_DIR.glob("session_*.json"):
        try:
            with open(filepath, "r") as f:
                data = json.load(f)
                sessions.append({
                    "id": data.get("id"),
                    "filepath": str(filepath),
                    "dataset": data.get("dataset"),
                    "split_subset": data.get("split_subset"),
                    "created_at": data.get("created_at"),
                    "answered_count": data.get("answered_count", 0),
                    "correct_count": data.get("correct_count", 0),
                    "incorrect_count": data.get("incorrect_count", 0),
                    "bookmarks": len(data.get("bookmarks", []))
                })
        except (json.JSONDecodeError, IOError):
            continue

    # Sort by creation date (newest first)
    sessions.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return sessions


def delete_current_session():
    """Delete the current session file."""
    if CURRENT_SESSION_FILE.exists():
        CURRENT_SESSION_FILE.unlink()


def load_session_by_id(session_id: str) -> Optional[Dict[str, Any]]:
    """Load an archived session by its ID.

    Args:
        session_id: The session ID (e.g., '20260214_120040')

    Returns:
        The session dict if found, None otherwise
    """
    ensure_sessions_dir()

    # Try direct ID match
    filepath = SESSIONS_DIR / f"session_{session_id}.json"
    if filepath.exists():
        try:
            with open(filepath, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None

    # Try partial match (search for sessions containing the ID)
    for fp in SESSIONS_DIR.glob("session_*.json"):
        if session_id in fp.stem:
            try:
                with open(fp, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                continue

    return None


def get_answered_rows(session: Dict[str, Any]) -> List[int]:
    """Get list of answered row indices in sorted order."""
    if session is None or "answers" not in session:
        return []
    return sorted([int(k) for k in session["answers"].keys()])


def get_next_answered_row(session: Dict[str, Any], current_idx: int, direction: int = 1) -> Optional[int]:
    """Find the next answered row in the given direction.

    Args:
        session: The current session
        current_idx: Current row index
        direction: 1 for next, -1 for previous

    Returns:
        The next answered row index, or None if none found
    """
    answered = get_answered_rows(session)
    if not answered:
        return None

    if direction == 1:
        # Find next answered row after current
        for idx in answered:
            if idx > current_idx:
                return idx
        # Wrap around to first
        return answered[0]
    else:
        # Find previous answered row before current
        for idx in reversed(answered):
            if idx < current_idx:
                return idx
        # Wrap around to last
        return answered[-1]
