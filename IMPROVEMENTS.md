# ZoleoTracker – Usability Improvement Findings

This document summarises a review of the ZoleoTracker codebase and proposes concrete improvements across architecture, language choice, data storage, reliability, observability, and developer experience.

---

## 1. Project Overview

ZoleoTracker is a Python script that:

1. Connects to a Gmail inbox via IMAP.
2. Searches for ZOLEO device check-in emails matching a hard-coded subject line.
3. Parses GPS location, timestamp, and Google Maps link from each email using regex.
4. Writes all check-ins to a flat TSV file (`location.csv`).
5. Reads that file back, compares the latest entry against a `previous_checkin.txt` timestamp file, and posts a Slack message if a new check-in is detected.

The tool is run manually or via a cron job every 30 minutes.

---

## 2. Current Pain Points

| # | Area | Issue |
|---|------|-------|
| 1 | **State management** | Deduplication relies on a plain text file (`previous_checkin.txt`) that must exist before first run and can easily become corrupted or lost. |
| 2 | **Data storage** | All location history is written to a TSV file (`location.csv`). This is fragile, has no concurrency protection, and makes querying/history difficult. A `databaseSQL.py` module exists but is **never called** from the main code path. |
| 3 | **Configuration** | Sensitive values (email credentials, Slack token) are passed as bare environment variables with no validation, defaults, or `.env` file support. The email subject line and folder are hard-coded constants in `config.py`. |
| 4 | **Error handling** | `parse_email_server()` silently swallows `AttributeError` by setting fields to `None`/`re.Match` objects instead of raising or logging. If a non-matching email is encountered `mail_content` may be undefined, causing a `NameError`. |
| 5 | **Reliability / scheduling** | The script is a one-shot cron job with no retry logic, no health-check endpoint, and no alerting if it fails. |
| 6 | **Incomplete `databaseSQL.py`** | `table_exists()` uses a MySQL `SHOW TABLES` statement against an SQLite connection, which will always fail. The `read_last_row()` query references a column `id` that is not defined in `create_table_if_not_exists()`. |
| 7 | **Testing** | Only three unit tests exist, all for `should_post()`. There are zero tests for email parsing, the database layer, or the Slack integration. |
| 8 | **Dependency sprawl** | `pandas` (a heavy analytics library) is used only to build a DataFrame and write a CSV. `pytest` is listed as a runtime dependency rather than a dev dependency. |
| 9 | **Scalability** | Every run fetches *all* emails from the inbox and rebuilds the entire CSV, even when only one new email has arrived. |
| 10 | **Notification channels** | Only Slack is supported. The README mentions "other social media (coming soon)" but no scaffolding exists for additional backends. |

---

## 3. Proposed Improvements

### 3.1 Replace the Flat File with a Proper Database

**Recommendation:** Finish and fix the existing `databaseSQL.py` SQLite integration, or migrate to a lightweight hosted database.

**Why:**
- SQLite removes the race condition risk of concurrent writes to `location.csv`.
- A single `SELECT MAX(checkin)` query replaces the `previous_checkin.txt` workaround.
- Historical data becomes queryable (e.g., "show all check-ins from last week").

**Specific fixes needed in `databaseSQL.py`:**
- Replace `SHOW TABLES LIKE tracker` with a proper SQLite query:
  `SELECT name FROM sqlite_master WHERE type='table' AND name='tracker'`
- Add an `id INTEGER PRIMARY KEY AUTOINCREMENT` column to the schema.
- Call `create_table_if_not_exists()` in `databaseSQL.py` before any reads/writes.
- Wire `databaseSQL.py` into `zoleotracker.py` in place of `to_csv`.

**Alternative – PostgreSQL / hosted database:**
For a multi-user or cloud deployment, replace SQLite with PostgreSQL (e.g., Supabase free tier, Railway, or Neon). The existing `pandas.to_sql` call in `append_dataframe()` is already compatible with SQLAlchemy and would require minimal changes.

---

### 3.2 Improve Configuration & Secret Management

**Recommendation:** Add environment variable validation and support a `.env` file.

- Use [`python-dotenv`](https://pypi.org/project/python-dotenv/) to load a `.env` file automatically so the shell wrapper (`runtracker.zsh`) is no longer needed.
- Validate required env vars at startup and exit with a clear error message if any are missing, rather than failing mid-run with an `AttributeError`.
- Move `CHECKIN_EMAIL_SUBJECT`, `EMAIL_SERVER`, and `EMAIL_FOLDER` to env vars or a config file (e.g., TOML/YAML) so the codebase does not need to change between deployments.

---

### 3.3 Fix and Harden Email Parsing

**Recommendation:** Refactor `parse_email_server()` for correctness and safety.

- Initialise `mail_content` to `None` before the loop and add a guard so emails without a matching subject are skipped cleanly.
- Raise (or log and skip) when regex patterns return `None` instead of silently appending `None` to lists.
- Add a `--since` filter to the IMAP `search` call (e.g., `SINCE {last_checkin_date}`) so only unprocessed emails are fetched, eliminating the full-inbox scan on every run.
- Consider replacing `html2text` + manual regex with a proper email MIME parser to avoid brittle text extraction.

---

### 3.4 Add Retry Logic and Health Monitoring

**Recommendation:** Wrap network calls (IMAP, Slack API) with retry/back-off and add an optional health-check ping.

- Use [`tenacity`](https://pypi.org/project/tenacity/) to retry transient IMAP and Slack failures with exponential back-off.
- Add a simple health-check: ping a service like [healthchecks.io](https://healthchecks.io) (free tier) at the end of each successful run so you can receive an alert if the cron job silently stops working.
- Log structured output (Python's `logging` module or [`structlog`](https://pypi.org/project/structlog/)) instead of using silent failures, so cron output is useful for debugging.

---

### 3.5 Expand Test Coverage

**Recommendation:** Add tests for all major code paths.

- Unit-test `parse_email_server()` using fixture `.eml` files (no live IMAP connection required via `unittest.mock.patch`).
- Unit-test `databaseSQL.py` CRUD functions against an in-memory SQLite database.
- Add an integration smoke-test (skippable when credentials are absent) that exercises the full flow end-to-end.
- Move `pytest` to `[tool.poetry.dependencies.dev]` and add `pytest-cov` for coverage reporting.

---

### 3.6 Add a Long-Running Daemon Mode (Replace Cron)

**Recommendation:** Optionally refactor the one-shot script into a daemon with an async polling loop.

Instead of a cron job, run ZoleoTracker as a persistent service:

- Use Python's `asyncio` + [`aioimaplib`](https://pypi.org/project/aioimaplib/) to maintain an IMAP IDLE connection. This pushes new emails to the script in real-time rather than polling every 30 minutes.
- Package as a `systemd` service or Docker container for easy deployment on a VPS or Raspberry Pi.
- Alternatively, deploy as a serverless function (AWS Lambda, Cloudflare Workers) triggered by a webhook or a scheduled EventBridge rule.

---

### 3.7 Support Multiple Notification Backends

**Recommendation:** Introduce a notification abstraction layer.

The README mentions social media support is "coming soon". A simple interface would enable this without a full rewrite:

```
NotificationBackend (abstract)
  ├── SlackBackend      (existing)
  ├── DiscordBackend    (new)
  ├── TwitterBackend    (new)
  └── WebhookBackend    (generic HTTP POST – new)
```

Each backend reads from the same database record and sends its own formatted message. New backends can be added without touching core parsing logic.

---

### 3.8 Rewrite in Go (Optional, Longer-Term)

**Recommendation:** A Go rewrite is a valid longer-term investment if operational simplicity is the primary goal.

**Benefits of Go:**
- Ships as a single static binary with no runtime dependencies – eliminates the Poetry/virtualenv setup step entirely.
- Lower memory footprint, faster startup – important for frequent cron-style execution.
- Strong standard library support for IMAP (`github.com/emersion/go-imap`), Slack (`github.com/slack-go/slack`), SQLite (`github.com/mattn/go-sqlite3`), and HTTP.
- Built-in concurrency primitives make the daemon/IMAP-IDLE pattern straightforward.

**Trade-offs:**
- Go's email parsing ecosystem is less mature than Python's `email` / `html2text` libraries.
- Rewriting removes the ability to use `pandas` and SQL Alchemy helpers (though these are heavier than necessary for this use case).
- It is a significant investment for a personal-use tool.

**Verdict:** If the project grows (multiple ZOLEO trackers, a web dashboard, etc.), a Go rewrite would pay dividends. For the current single-user use case, the Python improvements above deliver most of the value at a fraction of the effort.

---

### 3.9 Containerise the Application

**Recommendation:** Add a `Dockerfile` and `docker-compose.yml`.

This would:
- Remove the machine-specific cron/zsh setup entirely.
- Bundle the SQLite database volume as a Docker volume for persistence.
- Allow the service to be deployed to any cloud VM or Raspberry Pi with `docker compose up -d`.
- Simplify onboarding for new contributors.

---

### 3.10 Add a Simple Web Dashboard (Optional)

**Recommendation:** Expose a minimal read-only web UI to visualise the journey.

A lightweight framework like [FastAPI](https://fastapi.tiangolo.com/) (Python) or the Go standard library could serve:
- A map view (Leaflet.js + OpenStreetMap) showing the full route.
- A table of all check-ins.
- An RSS/Atom feed for check-ins.

This replaces the need to share Slack access with friends and family who just want to follow along.

---

## 4. Prioritised Recommendations

| Priority | Recommendation | Effort |
|----------|---------------|--------|
| 🔴 High | Fix `databaseSQL.py` bugs and wire it into the main code path | Small |
| 🔴 High | Fix undefined `mail_content` and silent `None` bugs in `parse_email_server()` | Small |
| 🔴 High | Add env-var validation at startup | Small |
| 🟠 Medium | Add IMAP `SINCE` filter to avoid full-inbox scans | Small |
| 🟠 Medium | Add retry logic for IMAP and Slack calls | Small |
| 🟠 Medium | Expand test coverage (email parsing, database layer) | Medium |
| 🟠 Medium | Add healthcheck.io ping for silent-failure detection | Small |
| 🟡 Low | Add notification abstraction layer for additional backends | Medium |
| 🟡 Low | Containerise with Docker | Medium |
| 🟡 Low | Add a simple web dashboard | Large |
| ⚪ Optional | Rewrite in Go | Large |

---

## 5. Conclusion

ZoleoTracker is a clean, focused personal utility. The core idea—email parsing → location tracking → Slack notification—is sound. The most impactful near-term improvements are:

1. **Fix and activate `databaseSQL.py`** to replace fragile flat-file state management.
2. **Harden the email parser** to handle edge cases without silent failures.
3. **Add startup validation** so misconfigured deployments fail fast with a clear message.

Longer-term, containerisation and a web dashboard would make the project significantly more shareable and reusable for others with ZOLEO devices.
