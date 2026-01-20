# asiabits Indices Generator

Automatically generates market indices graphics for the asiabits newsletter and sends them to Lark.

## How it works

- Runs daily at **6:00 AM Shanghai time** via GitHub Actions
- Fetches live market data from the indices API
- Generates DE and EN PNG images
- Sends images directly to the Lark group

## Setup

### 1. Create GitHub Repository

Create a new private repository and push this code.

### 2. Add Secrets

Go to Repository → Settings → Secrets and variables → Actions → New repository secret

Add these secrets:
- `LARK_APP_ID`: `cli_a9e5e0e4ad38de19`
- `LARK_APP_SECRET`: `ME2g5rYepm8gP0xRduXqAhU62OKgnWmw`

### 3. Enable Actions

Go to Repository → Actions → Enable workflows

### 4. Test

Click "Run workflow" to test manually.

## Manual Trigger

You can manually trigger the workflow anytime:
1. Go to Actions tab
2. Select "Generate Indices"
3. Click "Run workflow"

## Schedule

The workflow runs automatically at:
- 6:00 AM Shanghai time (GMT+8)
- 22:00 UTC (previous day)
- 23:00 German time (previous day)
