# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Garmin to Notion integration that automatically syncs fitness data from Garmin Connect to Notion databases. It supports activities, personal records, daily steps, and sleep data synchronization.

## Core Architecture

The project consists of 5 main Python scripts that work independently:

1. **garmin-activities.py** - Main sync script that fetches activities from Garmin Connect and creates/updates Notion database entries
2. **personal-records.py** - Extracts and tracks personal records (PRs) from Garmin activities (fastest times, longest distances, etc.)
3. **daily-steps.py** - Syncs daily step count data to Notion
4. **sleep-data.py** - Syncs sleep metrics and data to Notion
5. **cleanup-duplicates.py** - One-time utility script to remove duplicate activities from Notion database

Each script operates on specific Notion databases and requires different environment variables to function.

## Development Commands

### Running Scripts Locally
```bash
# Install dependencies
pip install -r requirements.txt

# Run individual scripts
python garmin-activities.py      # Sync activities
python personal-records.py      # Extract personal records
python daily-steps.py          # Sync daily steps
python sleep-data.py           # Sync sleep data
python cleanup-duplicates.py   # Remove duplicates (one-time use)
```

### Testing
The project does not include automated tests. Manual testing involves:
- Verifying Garmin Connect API connectivity
- Checking Notion database updates after script execution
- Validating data accuracy between Garmin and Notion

## Environment Configuration

All scripts require environment variables for authentication:

**Required for all scripts:**
- `GARMIN_EMAIL` - Garmin Connect account email
- `GARMIN_PASSWORD` - Garmin Connect account password
- `NOTION_TOKEN` - Notion API integration token

**Database-specific variables:**
- `NOTION_DB_ID` - Activities database ID (garmin-activities.py)
- `NOTION_PR_DB_ID` - Personal records database ID (personal-records.py)
- `NOTION_STEPS_DB_ID` - Daily steps database ID (daily-steps.py)
- `NOTION_SLEEP_DB_ID` - Sleep data database ID (sleep-data.py)

Environment variables can be loaded from `.env` file using `python-dotenv`.

## Key Dependencies

- **garminconnect** (>=0.2.19, <0.3) - Garmin Connect API client
- **notion-client** (==2.2.1) - Notion API client
- **pytz** (==2024.1) - Timezone handling for proper datetime conversion
- **withings-sync** (4.2.4) - Additional health data integration

## Data Flow Architecture

1. **Authentication Phase**: Each script authenticates with Garmin Connect using credentials
2. **Data Retrieval**: Scripts fetch relevant data from Garmin APIs (activities, sleep, steps, etc.)
3. **Data Processing**: Raw Garmin data is transformed to match Notion database schema
4. **Notion Integration**: Data is created/updated in appropriate Notion databases via API
5. **Duplicate Prevention**: Scripts check for existing entries before creating new ones

## Automation

The project includes GitHub Actions workflow (`.github/workflows/sync_garmin_to_notion.yml`) that:
- Runs daily at 1 AM UTC
- Executes all sync scripts in sequence
- Uses GitHub Secrets for environment variables
- Supports manual workflow dispatch for on-demand syncing

## Time Zone Considerations

Scripts handle timezone conversion from Garmin's UTC timestamps to local timezones:
- Default timezone: `America/Toronto` (garmin-activities.py)
- Configurable via `local_tz` variable in each script
- GitHub Actions uses `America/Montreal` timezone

## Activity Type Mapping

The project includes comprehensive activity type mapping with:
- Icon URLs for different activity types (from icons8.com)
- Activity type formatting and categorization
- Subtype to main type mapping for better organization
- Cover image URLs for personal records (from Unsplash)

## Notion Database Schema

Scripts expect specific Notion database properties:
- **Activities**: Date, Activity Type, Activity Name, Distance, Duration, etc.
- **Personal Records**: Record Type, Value, Date, Activity Link
- **Steps**: Date, Steps Count, Goal Status
- **Sleep**: Date, Total Sleep, Deep Sleep, REM Sleep, etc.

Refer to the Notion template linked in README.md for exact schema requirements.
