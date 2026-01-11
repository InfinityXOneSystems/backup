# GitHub Actions Workflow Setup

The automated backup workflow file is located at `.github/workflows/daily-backup.yml` but requires manual setup due to GitHub App permissions.

## Manual Setup Steps

1. Navigate to the repository on GitHub: https://github.com/InfinityXOneSystems/backup
2. Go to **Actions** tab
3. Click **"New workflow"**
4. Click **"set up a workflow yourself"**
5. Copy the content from `.github/workflows/daily-backup.yml` in this repository
6. Paste into the editor
7. Commit directly to the main branch

Alternatively, the workflow file can be pushed using a personal access token with `workflow` scope instead of the GitHub App token.

## Workflow File Location

`.github/workflows/daily-backup.yml`

The workflow is configured to run:
- **Daily at 2:00 AM UTC** (automatic)
- **On-demand** via manual trigger

Once set up, the automated backup system will run daily and store backups in the `backups/` directory.
