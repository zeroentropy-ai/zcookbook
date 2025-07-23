# Automated Monitoring & Alerting with ZeroEntropy

This guide demonstrates how to set up an automated workflow that monitors a folder for new documents, indexes them with ZeroEntropy, and sends an alert when new, relevant content is detected based on semantic queries.

## Overview

- **Monitor** a folder for new or updated files (PDF, TXT, CSV, etc.)
- **Index** new documents automatically using the ZeroEntropy API
- **Query** the new content for matches to a set of important topics or keywords
- **Alert** your team via email or Slack if relevant content is found

Some use cases for this could be:
- Keeping teams up-to-date with new, relevant information
- Automating knowledge discovery in shared drives or document repositories
- Surfacing important updates as soon as they appear

## Prerequisites

- Python 3.8+
- ZeroEntropy API key ([Get yours here](https://dashboard.zeroentropy.dev))
- `zeroentropy`, `python-dotenv`, `watchdog`, and `requests` Python packages
- (Optional) Email or Slack webhook for alerts

## Setup Instructions

1. **Install dependencies:**
   ```bash
   pip install zeroentropy python-dotenv watchdog requests
   ```
2. **Create a `.env` file** with your ZeroEntropy API key:
   ```bash
   ZEROENTROPY_API_KEY=your_api_key_here
   ```
3. **Configure your alerting method** in the script (email or Slack)
4. **Run the script:**
   ```bash
   python monitor_and_alert.py
   ```

## How it Works

- The script watches a specified folder for new or changed files.
- When a new file is detected, it is indexed with ZeroEntropy.
- The script runs a set of semantic queries against the new content.
- If any query returns a relevant result, an alert is sent to your team.

---

See `monitor_and_alert.py` for the implementation and configuration options. 