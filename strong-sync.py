import argparse
import csv
import os
from collections import OrderedDict
from datetime import datetime, timedelta

import pytz
from dotenv import load_dotenv
from notion_client import Client

local_tz = pytz.timezone("Europe/Zurich")

STRENGTH_ICON = "https://img.icons8.com/?size=100&id=107640&format=png&color=000000"


def parse_csv(csv_path):
    """Parse Strong CSV and group rows into workouts keyed by date timestamp."""
    workouts = OrderedDict()

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";", quotechar='"')
        for row in reader:
            if row["Set Order"] == "Rest Timer":
                continue

            date = row["Date"]
            if date not in workouts:
                workouts[date] = {
                    "date": date,
                    "name": row["Workout Name"],
                    "duration_sec": int(row["Duration (sec)"]),
                    "exercises": [],
                }

            workouts[date]["exercises"].append(
                {
                    "exercise": row["Exercise Name"],
                    "set_order": row["Set Order"],
                    "weight_kg": row.get("Weight (kg)", ""),
                    "reps": row.get("Reps", ""),
                    "distance_m": row.get("Distance (meters)", ""),
                    "seconds": row.get("Seconds", ""),
                    "notes": row.get("Notes", ""),
                }
            )

    return workouts


def group_exercises(exercises):
    """Group exercise rows by name, maintaining order."""
    groups = OrderedDict()
    for ex in exercises:
        name = ex["exercise"]
        if name not in groups:
            groups[name] = {"sets": [], "notes": []}
        if ex["set_order"] == "Note":
            groups[name]["notes"].append(ex["notes"])
        else:
            groups[name]["sets"].append(ex)
    return groups


def workout_exists(client, database_id, workout_date):
    """Check if a workout already exists by its strong-{timestamp} ID."""
    strong_id = f"strong-{workout_date}"
    try:
        query = client.databases.query(
            database_id=database_id,
            filter={"property": "Garmin ID", "multi_select": {"contains": strong_id}},
        )
        if query["results"]:
            return query["results"][0]
    except Exception as e:
        print(f"Error checking for existing workout: {e}")
    return None


def format_time(total_seconds):
    """Format seconds into mm:ss or h:mm:ss."""
    total_seconds = int(float(total_seconds))
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes}:{seconds:02d}"


def format_set(ex):
    """Format a single set's weight/reps display values."""
    if ex["distance_m"]:
        distance_km = float(ex["distance_m"]) / 1000
        weight_display = f"{distance_km:.2f} km"
        reps_display = format_time(ex["seconds"]) if ex["seconds"] else ""
    elif ex["seconds"] and not ex["weight_kg"]:
        weight_display = ""
        reps_display = format_time(ex["seconds"])
    else:
        weight = float(ex["weight_kg"]) if ex["weight_kg"] else 0
        weight_display = "BW" if weight == 0 else f"{weight:g}"
        reps_display = ex["reps"] if ex["reps"] else ""
    return weight_display, reps_display


def build_page_content(exercises):
    """Build Notion blocks with a heading and table per exercise."""
    blocks = []
    exercise_groups = group_exercises(exercises)

    for i, (exercise_name, data) in enumerate(exercise_groups.items()):
        # Heading per exercise
        blocks.append(
            {
                "type": "heading_3",
                "heading_3": {"rich_text": [{"type": "text", "text": {"content": exercise_name}}]},
            }
        )

        # Notes as italic paragraph
        for note in data["notes"]:
            blocks.append(
                {
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": note},
                                "annotations": {"italic": True},
                            }
                        ]
                    },
                }
            )

        # Table for sets
        if data["sets"]:
            headers = ["Set", "Weight (kg)", "Reps"]
            header_cells = [[{"type": "text", "text": {"content": h}}] for h in headers]
            table_rows = [{"type": "table_row", "table_row": {"cells": header_cells}}]

            for s in data["sets"]:
                weight_display, reps_display = format_set(s)
                cells = [
                    [{"type": "text", "text": {"content": c}}]
                    for c in [s["set_order"], weight_display, reps_display]
                ]
                table_rows.append({"type": "table_row", "table_row": {"cells": cells}})

            blocks.append(
                {
                    "type": "table",
                    "table": {
                        "table_width": 3,
                        "has_column_header": True,
                        "has_row_header": False,
                        "children": table_rows,
                    },
                }
            )

        # Divider between exercises (not after last)
        if i < len(exercise_groups) - 1:
            blocks.append({"type": "divider", "divider": {}})

    return blocks


def replace_page_content(client, page_id, blocks):
    """Delete existing page content blocks and append new ones."""
    existing = client.blocks.children.list(block_id=page_id)
    for block in existing["results"]:
        client.blocks.delete(block_id=block["id"])
    while existing.get("has_more"):
        existing = client.blocks.children.list(
            block_id=page_id, start_cursor=existing["next_cursor"]
        )
        for block in existing["results"]:
            client.blocks.delete(block_id=block["id"])

    client.blocks.children.append(block_id=page_id, children=blocks)


def make_workout_dates(workout):
    """Compute localized start/end datetimes for a workout."""
    start_dt = local_tz.localize(datetime.strptime(workout["date"], "%Y-%m-%d %H:%M:%S"))
    end_dt = start_dt + timedelta(seconds=workout["duration_sec"])
    return start_dt, end_dt


def create_workout_page(client, database_id, workout):
    """Create a Notion page for a workout with per-exercise content."""
    start_dt, end_dt = make_workout_dates(workout)
    strong_id = f"strong-{workout['date']}"

    properties = {
        "Activity Name": {"title": [{"text": {"content": workout["name"]}}]},
        "Date": {"date": {"start": start_dt.isoformat(), "end": end_dt.isoformat()}},
        "Activity Type": {"select": {"name": "Strength"}},
        "Subactivity Type": {"select": {"name": "Strength Training"}},
        "Duration (min)": {"number": round(workout["duration_sec"] / 60, 2)},
        "Distance (km)": {"number": 0},
        "Calories": {"number": 0},
        "Avg Pace": {"rich_text": [{"text": {"content": ""}}]},
        "Avg Power": {"number": 0},
        "Max Power": {"number": 0},
        "Training Effect": {"select": {"name": "Unknown"}},
        "Aerobic": {"number": 0},
        "Aerobic Effect": {"select": {"name": "Unknown"}},
        "Anaerobic": {"number": 0},
        "Anaerobic Effect": {"select": {"name": "Unknown"}},
        "PR": {"checkbox": False},
        "Fav": {"checkbox": False},
        "Garmin ID": {"multi_select": [{"name": strong_id}]},
    }

    page = client.pages.create(
        parent={"database_id": database_id},
        properties=properties,
        icon={"type": "external", "external": {"url": STRENGTH_ICON}},
    )

    blocks = build_page_content(workout["exercises"])
    client.blocks.children.append(block_id=page["id"], children=blocks)
    return page["id"]


def update_workout(client, existing_page, workout):
    """Update date and rebuild page content for an existing workout."""
    start_dt, end_dt = make_workout_dates(workout)

    client.pages.update(
        page_id=existing_page["id"],
        properties={
            "Date": {"date": {"start": start_dt.isoformat(), "end": end_dt.isoformat()}},
        },
    )

    blocks = build_page_content(workout["exercises"])
    replace_page_content(client, existing_page["id"], blocks)


# --- Exercise Progress Database ---


def get_or_create_exercise_db(client, activities_db_id):
    """Get exercise DB ID from env, or auto-create one."""
    exercise_db_id = os.getenv("NOTION_EXERCISE_DB_ID")
    if exercise_db_id:
        return exercise_db_id

    # Determine parent from activities database
    db_info = client.databases.retrieve(activities_db_id)
    parent = db_info["parent"]

    if parent["type"] != "page_id":
        print("Cannot auto-create exercise database (activities DB parent is not a page).")
        print("Create the database manually and set NOTION_EXERCISE_DB_ID in .env")
        return None

    exercise_db = client.databases.create(
        parent={"type": "page_id", "page_id": parent["page_id"]},
        title=[{"type": "text", "text": {"content": "Exercise Progress"}}],
        icon={"type": "external", "external": {"url": STRENGTH_ICON}},
        properties={
            "Exercise": {"title": {}},
            "Date": {"date": {}},
            "Max Weight (kg)": {"number": {"format": "number"}},
            "Total Volume (kg)": {"number": {"format": "number"}},
            "Sets": {"number": {"format": "number"}},
            "Total Reps": {"number": {"format": "number"}},
            "Workout": {"rich_text": {}},
        },
    )

    db_id = exercise_db["id"]
    print(f"\nCreated 'Exercise Progress' database: {db_id}")
    print(f"Add to .env:  NOTION_EXERCISE_DB_ID={db_id}\n")
    return db_id


def exercise_entry_exists(client, db_id, date_str, exercise_name):
    """Check if an exercise entry exists for this date and exercise name."""
    query = client.databases.query(
        database_id=db_id,
        filter={
            "and": [
                {"property": "Exercise", "title": {"equals": exercise_name}},
                {"property": "Date", "date": {"on_or_after": date_str}},
                {"property": "Date", "date": {"on_or_before": date_str}},
            ]
        },
    )
    return query["results"][0] if query["results"] else None


def sync_exercise_entries(client, db_id, workout):
    """Create or update exercise summary rows for progress tracking."""
    start_dt, _ = make_workout_dates(workout)
    date_only = start_dt.strftime("%Y-%m-%d")
    date_iso = start_dt.isoformat()

    exercise_groups = group_exercises(workout["exercises"])

    for exercise_name, data in exercise_groups.items():
        sets = data["sets"]
        if not sets:
            continue

        max_weight = 0
        total_volume = 0
        total_reps = 0

        for s in sets:
            weight = float(s["weight_kg"]) if s["weight_kg"] else 0
            reps = int(s["reps"]) if s["reps"] else 0
            max_weight = max(max_weight, weight)
            total_volume += weight * reps
            total_reps += reps

        properties = {
            "Exercise": {"title": [{"text": {"content": exercise_name}}]},
            "Date": {"date": {"start": date_iso}},
            "Max Weight": {"number": max_weight},
            "Total Volumn": {"number": round(total_volume, 1)},
            "Sets": {"number": len(sets)},
            "Total Reps": {"number": total_reps},
            "Workouts": {"rich_text": [{"text": {"content": workout["name"]}}]},
        }

        existing = exercise_entry_exists(client, db_id, date_only, exercise_name)
        if existing:
            client.pages.update(page_id=existing["id"], properties=properties)
        else:
            client.pages.create(
                parent={"database_id": db_id},
                properties=properties,
                icon={"type": "external", "external": {"url": STRENGTH_ICON}},
            )


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(description="Sync Strong app CSV to Notion")
    parser.add_argument("--csv", help="Path to Strong CSV export file")
    parser.add_argument(
        "--rebuild", action="store_true", help="Rebuild page content for existing workouts"
    )
    args = parser.parse_args()

    csv_path = args.csv or os.getenv("STRONG_CSV_PATH")
    if not csv_path:
        print("Error: Provide CSV path via --csv argument or STRONG_CSV_PATH env var")
        return

    notion_token = os.getenv("NOTION_TOKEN")
    database_id = os.getenv("NOTION_DB_ID")

    if not notion_token or not database_id:
        print("Error: NOTION_TOKEN and NOTION_DB_ID environment variables required")
        return

    client = Client(auth=notion_token)

    # Get or create exercise progress database
    exercise_db_id = get_or_create_exercise_db(client, database_id)

    # Parse CSV
    workouts = parse_csv(csv_path)
    print(f"Found {len(workouts)} workouts in CSV")

    created = 0
    updated = 0
    skipped = 0

    for date, workout in workouts.items():
        existing = workout_exists(client, database_id, date)
        if existing:
            if args.rebuild:
                update_workout(client, existing, workout)
                print(f"  Rebuilt: {workout['name']} - {date}")
                updated += 1
            else:
                print(f"  Skipped: {workout['name']} - {date}")
                skipped += 1
        else:
            create_workout_page(client, database_id, workout)
            print(f"  Created: {workout['name']} - {date}")
            created += 1

        # Always sync exercise entries if DB available
        if exercise_db_id:
            sync_exercise_entries(client, exercise_db_id, workout)

    print(f"\nDone: {created} created, {updated} rebuilt, {skipped} skipped")


if __name__ == "__main__":
    main()
