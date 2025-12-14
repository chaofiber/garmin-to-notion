# Garmin Session Authentication Setup

This guide helps you set up session-based authentication to avoid Garmin security alerts when using GitHub Actions.

## Why Session Authentication?

When GitHub Actions runs your scripts from different IP locations, Garmin detects this as suspicious activity and triggers security measures (password reset requests). Session authentication solves this by:
- Using a persistent session token instead of logging in each time
- Reducing the frequency of actual login attempts
- Maintaining the same "session" across different GitHub runners

## Setup Steps

### 1. Generate Session Locally (One-time setup)

Run this command on your local machine to create an initial session:

```bash
python garmin_session_auth.py login
```

This will:
- Login to Garmin using your credentials
- Save the session to `.garmin_session/session.pkl`
- The session remains valid for ~30 days

### 2. Export Session for GitHub

After creating the session, export it for GitHub:

```bash
python garmin_session_auth.py export
```

This will display a base64-encoded session string. Copy the entire string.

### 3. Add to GitHub Secrets

1. Go to your GitHub repository
2. Navigate to Settings → Secrets and variables → Actions
3. Click "New repository secret"
4. Name: `GARMIN_SESSION`
5. Value: Paste the base64 string from step 2
6. Click "Add secret"

### 4. Update GitHub Actions Workflow

Your workflow should now use the session. Add this to your `.github/workflows/sync_garmin_to_notion.yml`:

```yaml
env:
  GARMIN_EMAIL: ${{ secrets.GARMIN_EMAIL }}
  GARMIN_PASSWORD: ${{ secrets.GARMIN_PASSWORD }}
  GARMIN_SESSION: ${{ secrets.GARMIN_SESSION }}  # Add this line
  NOTION_TOKEN: ${{ secrets.NOTION_TOKEN }}
  # ... other secrets
```

## How It Works

1. **First Run**: The script checks for `GARMIN_SESSION` environment variable
2. **Session Found**: Uses the session token to authenticate (no password needed)
3. **Session Invalid/Missing**: Falls back to email/password login
4. **Auto-refresh**: If session is older than 30 days, it refreshes automatically

## Testing

Test your session locally:

```bash
python garmin_session_auth.py test
```

This will verify the session is working and show the authenticated user.

## Maintenance

### Refresh Session (Monthly)

Sessions expire after ~30 days. To refresh:

1. Run locally: `python garmin_session_auth.py login`
2. Export: `python garmin_session_auth.py export`
3. Update the `GARMIN_SESSION` secret in GitHub

### If You Get Security Alerts

If you still get security alerts:
1. The session may have expired - refresh it
2. Garmin may have invalidated the session - create a new one
3. Consider setting up a dedicated device/app password in Garmin if available

## Troubleshooting

- **Session not working**: Delete `.garmin_session/` folder and create a new session
- **Import error**: Make sure `garmin_session_auth.py` is in the same directory as `garmin-activities.py`
- **GitHub Actions failing**: Check the Actions logs for authentication errors

## Security Notes

- Never commit the `.garmin_session/` folder to git (add it to `.gitignore`)
- The session file has restricted permissions (600) for security
- GitHub Secrets are encrypted and safe to use
- Consider rotating sessions periodically for better security
