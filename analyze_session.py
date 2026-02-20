#!/usr/bin/env python3
"""
Session analysis script for AI2Thor Dataset Viewer.
Analyzes saved quiz sessions and generates reports.

Usage:
    python analyze_session.py                    # Analyze all sessions
    python analyze_session.py --session <id>    # Analyze specific session
    python analyze_session.py --current         # Analyze current session
    python analyze_session.py --list            # List all sessions
"""

import json
import argparse
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime

SESSIONS_DIR = Path("./sessions")
CURRENT_SESSION_FILE = SESSIONS_DIR / "current_session.json"


def load_session(filepath: Path) -> dict:
    """Load a session from file."""
    with open(filepath, "r") as f:
        return json.load(f)


def list_all_sessions():
    """List all available sessions."""
    print("\n" + "=" * 70)
    print("AVAILABLE SESSIONS")
    print("=" * 70)

    sessions = []

    # Current session
    if CURRENT_SESSION_FILE.exists():
        session = load_session(CURRENT_SESSION_FILE)
        sessions.append(("current", CURRENT_SESSION_FILE, session))

    # Archived sessions
    for filepath in sorted(SESSIONS_DIR.glob("session_*.json"), reverse=True):
        session = load_session(filepath)
        sessions.append((session.get("id", "unknown"), filepath, session))

    if not sessions:
        print("No sessions found.")
        return

    print(f"\n{'ID':<20} {'Dataset':<35} {'Answered':<12} {'Accuracy':<10} {'Bookmarks':<10}")
    print("-" * 90)

    for session_id, filepath, session in sessions:
        dataset = session.get("dataset", "Unknown")[:33]
        answered = session.get("answered_count", 0)
        total = session.get("total_questions", 0)
        correct = session.get("correct_count", 0)
        bookmarks = len(session.get("bookmarks", []))

        accuracy = (correct / answered * 100) if answered > 0 else 0

        label = "current" if filepath == CURRENT_SESSION_FILE else session_id
        print(f"{label:<20} {dataset:<35} {answered}/{total:<10} {accuracy:>6.1f}%    {bookmarks:<10}")

    print("-" * 90)
    print(f"Total sessions: {len(sessions)}")


def analyze_session(session: dict, verbose: bool = True):
    """Analyze a single session and print report."""
    print("\n" + "=" * 70)
    print("SESSION ANALYSIS REPORT")
    print("=" * 70)

    # Basic info
    print(f"\nSession ID: {session.get('id', 'N/A')}")
    print(f"Dataset: {session.get('dataset', 'N/A')}")
    print(f"Split/Subset: {session.get('split_subset', 'N/A')}")
    print(f"Created: {session.get('created_at', 'N/A')}")
    print(f"Last Updated: {session.get('updated_at', 'N/A')}")

    # Summary stats
    total = session.get("total_questions", 0)
    answered = session.get("answered_count", 0)
    correct = session.get("correct_count", 0)
    incorrect = session.get("incorrect_count", 0)
    bookmarks = session.get("bookmarks", [])

    accuracy = (correct / answered * 100) if answered > 0 else 0
    progress = (answered / total * 100) if total > 0 else 0

    print("\n" + "-" * 40)
    print("SUMMARY STATISTICS")
    print("-" * 40)
    print(f"Total Questions: {total}")
    print(f"Answered: {answered} ({progress:.1f}%)")
    print(f"Remaining: {total - answered}")
    print(f"Correct: {correct}")
    print(f"Incorrect: {incorrect}")
    print(f"Accuracy: {accuracy:.1f}%")
    print(f"Bookmarks: {len(bookmarks)}")

    # Analyze answers
    answers = session.get("answers", {})

    if answers:
        print("\n" + "-" * 40)
        print("ANSWER BREAKDOWN")
        print("-" * 40)

        # By correctness
        correct_answers = []
        incorrect_answers = []

        for row_idx, answer_data in answers.items():
            if answer_data.get("is_correct"):
                correct_answers.append((int(row_idx), answer_data))
            else:
                incorrect_answers.append((int(row_idx), answer_data))

        # Incorrect answers details
        if incorrect_answers:
            print(f"\n❌ INCORRECT ANSWERS ({len(incorrect_answers)}):")
            print("-" * 40)

            # Group by query object if available
            by_object = defaultdict(list)
            for row_idx, data in incorrect_answers:
                obj = data.get("query_object", "unknown")
                by_object[obj].append((row_idx, data))

            for obj, items in sorted(by_object.items()):
                print(f"\n  {obj}:")
                for row_idx, data in items:
                    user_ans = data.get("user_answer", "?")
                    correct_ans = data.get("correct_answer", "?")
                    print(f"    Row {row_idx + 1}: You={user_ans}, Correct={correct_ans}")

            # List all incorrect indices
            print(f"\n  All incorrect row indices: {sorted([r for r, _ in incorrect_answers])}")

        # Correct answers summary
        if correct_answers and verbose:
            print(f"\n✓ CORRECT ANSWERS ({len(correct_answers)}):")
            print(f"  Row indices: {sorted([r for r, _ in correct_answers])}")

        # Analysis by query object
        if any(a.get("query_object") for a in answers.values()):
            print("\n" + "-" * 40)
            print("ACCURACY BY OBJECT TYPE")
            print("-" * 40)

            object_stats = defaultdict(lambda: {"correct": 0, "incorrect": 0})
            for row_idx, data in answers.items():
                obj = data.get("query_object", "unknown")
                if data.get("is_correct"):
                    object_stats[obj]["correct"] += 1
                else:
                    object_stats[obj]["incorrect"] += 1

            print(f"\n{'Object':<25} {'Correct':<10} {'Incorrect':<10} {'Accuracy':<10}")
            print("-" * 55)

            for obj, stats in sorted(object_stats.items(), key=lambda x: x[1]["incorrect"], reverse=True):
                c = stats["correct"]
                i = stats["incorrect"]
                acc = c / (c + i) * 100 if (c + i) > 0 else 0
                print(f"{obj:<25} {c:<10} {i:<10} {acc:>6.1f}%")

    # Bookmarks
    if bookmarks:
        print("\n" + "-" * 40)
        print(f"BOOKMARKED ROWS ({len(bookmarks)})")
        print("-" * 40)
        print(f"Indices: {sorted(bookmarks)}")

        # Show bookmark details if answers exist
        print("\nBookmark details:")
        for bm in sorted(bookmarks):
            bm_str = str(bm)
            if bm_str in answers:
                data = answers[bm_str]
                status = "✓" if data.get("is_correct") else "✗"
                obj = data.get("query_object", "")
                print(f"  Row {bm + 1}: {status} {obj}")
            else:
                print(f"  Row {bm + 1}: (not answered)")

    print("\n" + "=" * 70)


def export_session_csv(session: dict, output_file: str = None):
    """Export session answers to CSV."""
    if output_file is None:
        output_file = f"session_{session.get('id', 'export')}.csv"

    answers = session.get("answers", {})

    with open(output_file, "w") as f:
        f.write("row_idx,question,user_answer,correct_answer,is_correct,query_object,timestamp\n")

        for row_idx, data in sorted(answers.items(), key=lambda x: int(x[0])):
            question = data.get("question", "").replace('"', '""')
            user_ans = data.get("user_answer", "")
            correct_ans = data.get("correct_answer", "")
            is_correct = data.get("is_correct", False)
            query_obj = data.get("query_object", "")
            timestamp = data.get("timestamp", "")

            f.write(f'{row_idx},"{question}",{user_ans},{correct_ans},{is_correct},{query_obj},{timestamp}\n')

    print(f"Exported to: {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Analyze quiz sessions")
    parser.add_argument("--session", "-s", type=str, help="Session ID to analyze")
    parser.add_argument("--current", "-c", action="store_true", help="Analyze current session")
    parser.add_argument("--list", "-l", action="store_true", help="List all sessions")
    parser.add_argument("--export", "-e", action="store_true", help="Export session to CSV")
    parser.add_argument("--all", "-a", action="store_true", help="Analyze all sessions")
    parser.add_argument("--quiet", "-q", action="store_true", help="Less verbose output")

    args = parser.parse_args()

    if not SESSIONS_DIR.exists():
        print("No sessions directory found. Run the viewer first to create a session.")
        return

    if args.list:
        list_all_sessions()
        return

    if args.current:
        if not CURRENT_SESSION_FILE.exists():
            print("No current session found.")
            return
        session = load_session(CURRENT_SESSION_FILE)
        analyze_session(session, verbose=not args.quiet)
        if args.export:
            export_session_csv(session)
        return

    if args.session:
        filepath = SESSIONS_DIR / f"session_{args.session}.json"
        if not filepath.exists():
            print(f"Session not found: {args.session}")
            return
        session = load_session(filepath)
        analyze_session(session, verbose=not args.quiet)
        if args.export:
            export_session_csv(session)
        return

    if args.all:
        # Analyze all sessions
        for filepath in sorted(SESSIONS_DIR.glob("session_*.json")):
            session = load_session(filepath)
            analyze_session(session, verbose=not args.quiet)
            print("\n")
        return

    # Default: analyze current session if exists, otherwise list
    if CURRENT_SESSION_FILE.exists():
        session = load_session(CURRENT_SESSION_FILE)
        analyze_session(session, verbose=not args.quiet)
    else:
        list_all_sessions()


if __name__ == "__main__":
    main()
