# Workout Sync to Notion

Automatically sync fitness data from multiple sources to Notion databases. Supports Garmin Connect activities, personal records, daily steps, sleep data, and Strong app strength training workouts.

## Features

- Sync Garmin activities with detailed metrics (distance, pace, heart rate, training effect)
- Track personal records (fastest 1K, longest ride, etc.)
- Sync daily steps and sleep data
- Sync Strong app strength training workouts with per-exercise detail tables
- Track exercise progress over time (max weight, total volume, reps) for charting
- Automated daily sync via GitHub Actions
- Strong CSV auto-download from Google Drive (pairs with FolderSync on Android)
- Duplicate detection — safe to re-run at any time

## Data Sources

| Source | Script | What it syncs |
|---|---|---|
| Garmin Connect | `garmin-activities.py` | Activities, metrics, training effects |
| Garmin Connect | `personal-records.py` | Personal records (fastest, longest, etc.) |
| Garmin Connect | `daily-steps.py` | Daily step counts |
| Garmin Connect | `sleep-data.py` | Sleep metrics (deep, REM, light) |
| Strong App | `strong-sync.py` | Strength workouts with exercise tables |
| Google Drive | `download_strong_csv.py` | Downloads latest Strong CSV export |

## Prerequisites

- A Notion account with API access
- A Garmin Connect account
- (Optional) Strong app for strength training tracking
- (Optional) Google Cloud service account for automated Strong CSV download

## Getting Started

### 1. Fork this Repository

### 2. Duplicate the [Notion Template](https://www.notion.so/templates/fitness-tracker-738)

Save the database IDs from each database URL (the string before `?v=`).

### 3. Create a Notion Integration

- Go to [Notion Integrations](https://www.notion.so/profile/integrations)
- [Create](https://developers.notion.com/docs/create-a-notion-integration) a new integration and copy the token
- [Share](https://www.notion.so/help/add-and-manage-connections-with-the-api#enterprise-connection-settings) the integration with each database

### 4. Set Environment Variables

For local use, create a `.env` file:

```env
GARMIN_EMAIL=your_email
GARMIN_PASSWORD=your_password
NOTION_TOKEN=your_notion_token
NOTION_DB_ID=activities_database_id
NOTION_PR_DB_ID=personal_records_database_id
NOTION_STEPS_DB_ID=steps_database_id        # optional
NOTION_SLEEP_DB_ID=sleep_database_id        # optional
NOTION_EXERCISE_DB_ID=exercise_database_id  # optional, for Strong progress tracking
```

For GitHub Actions, add these as repository secrets under **Settings > Secrets and variables > Actions**.

### 5. Run Scripts

```bash
pip install -r requirements.txt

python garmin-activities.py                    # Sync Garmin activities
python personal-records.py                     # Extract personal records
python daily-steps.py                          # Sync daily steps
python sleep-data.py                           # Sync sleep data
python strong-sync.py --csv export.csv         # Sync Strong workouts
python strong-sync.py --csv export.csv --rebuild  # Rebuild page content
```

### 6. Strong App Setup (Optional)

To automate Strong workout syncing:

1. **Google Cloud**: Create a service account, enable Google Drive API, download the JSON key
2. **Google Drive**: Create a `Strong` folder, share it with the service account email
3. **Android**: Install FolderSync, configure it to upload Strong CSV exports to the Google Drive folder
4. **GitHub Secrets**: Add `GOOGLE_SERVICE_ACCOUNT_JSON`, `GOOGLE_DRIVE_FOLDER_ID`, and `NOTION_EXERCISE_DB_ID`

The GitHub Actions workflow will automatically download the latest CSV and sync new workouts.

## Automation

The included GitHub Actions workflow (`.github/workflows/sync_garmin_to_notion.yml`) runs every 15 minutes during daytime (Zurich timezone) and:

1. Syncs Garmin activities
2. Downloads the latest Strong CSV from Google Drive
3. Syncs new Strong workouts to Notion

Manual runs are also supported via workflow dispatch.

## Acknowledgements

- [cyberjunky/python-garminconnect](https://github.com/cyberjunky/python-garminconnect) for the Garmin Connect API client
- [n-kratz/garmin-notion](https://github.com/n-kratz/garmin-notion) for the original inspiration
- Originally forked from [chloevoyer/garmin-to-notion](https://github.com/chloevoyer/garmin-to-notion)

## License

This project is licensed under the MIT License. See the LICENSE file for details.
