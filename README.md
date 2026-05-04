# PostgreSQL Data Migration Counter & Reporter

A Python-based tool suite for tracking record counts during PostgreSQL database migrations, detecting data discrepancies, and generating detailed comparison reports.

## Features

✓ **Pre & Post-Migration Counting** — Count all records in every table before and after migration  
✓ **Minimal Dependencies** — Uses only `psycopg2` for database connection; stdlib for everything else  
✓ **Parallel Processing** — Uses ThreadPoolExecutor to count tables in parallel (10 workers by default)  
✓ **Flexible Configuration** — Supports CLI args, environment variables, and JSON config files  
✓ **Detailed Reporting** — Generates interactive HTML and CSV reports highlighting discrepancies  
✓ **Record Loss Detection** — Automatically flags tables where records went missing  

## Installation

### Prerequisites

- Python 3.6+
- PostgreSQL database (accessible via network or local connection)
- `psycopg2` package

### Setup

1. Clone/download this repository:
   ```bash
   cd pgsql-counter
   ```

2. Install the required PostgreSQL adapter:
   ```bash
   pip install psycopg2-binary
   ```
   
   Or if you prefer the full `psycopg2` package (requires PostgreSQL dev libraries):
   ```bash
   pip install psycopg2
   ```

3. (Optional) Create a config file from the template:
   ```bash
   cp .migration_config.example.json ~/.migration_config.json
   # Edit with your database credentials
   ```

## Usage

### 1. Pre-Migration Count

Run a record count snapshot **before** your migration:

```bash
# Using CLI arguments
python migration_counter.py --mode pre --host localhost --user postgres --password secret --database mydb

# Using environment variables
export DB_HOST=localhost
export DB_USER=postgres
export DB_PASSWORD=secret
export DB_NAME=mydb
python migration_counter.py --mode pre

# Using config file
python migration_counter.py --mode pre --config ~/.migration_config.json

# Save output to a specific directory
python migration_counter.py --mode pre --output-dir ./reports
```

**Output:** `pre_migration_count.json` with timestamps and record counts for all tables.

### 2. Perform Your Migration

Run your database migration scripts, data transformation, or whatever migration procedure you need.

### 3. Post-Migration Count

Run the same count after migration is complete:

```bash
python migration_counter.py --mode post --config ~/.migration_config.json --output-dir ./reports
```

**Output:** `post_migration_count.json`

### 4. Generate Comparison Report

Compare the two snapshots and generate a detailed report:

```bash
# Generate both HTML and CSV reports
python migration_reporter.py \
  --pre ./reports/pre_migration_count.json \
  --post ./reports/post_migration_count.json \
  --output both

# Generate only HTML
python migration_reporter.py \
  --pre pre_migration_count.json \
  --post post_migration_count.json \
  --output html

# Generate only CSV
python migration_reporter.py \
  --pre pre_migration_count.json \
  --post post_migration_count.json \
  --output csv

# Custom output filenames and directory
python migration_reporter.py \
  --pre pre_migration_count.json \
  --post post_migration_count.json \
  --output-dir ./reports \
  --html-file migration_report_v1.html \
  --csv-file migration_report_v1.csv
```

**Output:** 
- `migration_report.html` — Interactive HTML table with summary and detailed comparison
- `migration_report.csv` — Machine-readable CSV format with summary metadata

## Configuration Methods

### Priority Order

Configuration is loaded in this priority order (highest to lowest):
1. **CLI arguments** (e.g., `--host`, `--user`, `--password`, `--database`)
2. **Environment variables** (e.g., `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`)
3. **Config file** (JSON, default: `~/.migration_config.json`)
4. **Defaults** (localhost, postgres, postgres database)

Example with all three overlapping:

```bash
# Config file has host=prod.example.com, user=admin
# Environment variables specify DB_HOST=staging.example.com
# CLI argument specifies --database testdb
# Result: host=staging.example.com (env wins over config), user=admin (from config), database=testdb (CLI wins)

export DB_HOST=staging.example.com
python migration_counter.py --mode pre --config ~/.migration_config.json --database testdb
```

### Using CLI Arguments

```bash
python migration_counter.py --mode pre \
  --host db.example.com \
  --port 5432 \
  --user migration_user \
  --password "P@ssw0rd!" \
  --database production_db
```

### Using Environment Variables

```bash
export DB_HOST=db.example.com
export DB_PORT=5432
export DB_USER=migration_user
export DB_PASSWORD=P@ssw0rd!
export DB_NAME=production_db

python migration_counter.py --mode pre
```

### Using Config File

Create `~/.migration_config.json`:

```json
{
  "host": "db.example.com",
  "port": 5432,
  "user": "migration_user",
  "password": "P@ssw0rd!",
  "database": "production_db"
}
```

Then run:

```bash
python migration_counter.py --mode pre --config ~/.migration_config.json
```

## Output Files

### Pre/Post-Migration Count Files

Example `pre_migration_count.json`:

```json
{
  "timestamp": "2026-05-01T14:30:45.123456",
  "mode": "pre",
  "tables": {
    "public.users": 15000,
    "public.orders": 42500,
    "public.products": 800,
    "public.order_items": 125000
  },
  "total_records": 183300,
  "table_count": 4
}
```

### HTML Report

The HTML report includes:
- **Summary section** with total records (pre/post), net change, table counts
- **Critical warnings** if records were lost
- **Color-coded table** showing per-table comparisons:
  - 🟢 **Green** (MATCH) — Record count unchanged
  - 🟡 **Yellow** (INCREASED) — Record count increased
  - 🔴 **Red** (LOST) — Record count decreased (critical!)
- **Metadata footer** with timestamps

Open `migration_report.html` in any web browser.

### CSV Report

The CSV includes:
- Summary statistics as header comments
- Table: `Table Name | Pre-Migration | Post-Migration | Difference | Status`
- Machine-readable format suitable for further analysis or importing into spreadsheets

## Example Workflow

```bash
# 1. Create output directory
mkdir -p migration_reports

# 2. Pre-migration count (takes ~30 seconds for large databases with parallel workers)
python migration_counter.py \
  --mode pre \
  --config ~/.migration_config.json \
  --output-dir migration_reports \
  --workers 15

# 3. Run your migration (data sync, transform, etc.)
# ... your migration scripts ...

# 4. Post-migration count (same as pre)
python migration_counter.py \
  --mode post \
  --config ~/.migration_config.json \
  --output-dir migration_reports

# 5. Generate reports
python migration_reporter.py \
  --pre migration_reports/pre_migration_count.json \
  --post migration_reports/post_migration_count.json \
  --output-dir migration_reports

# 6. Review reports
# Open migration_reports/migration_report.html in browser
# Or inspect migration_reports/migration_report.csv in Excel/terminal
```

## Advanced Options

### Parallel Workers

Control how many tables are counted in parallel:

```bash
# Use 20 workers for faster counting on large systems
python migration_counter.py --mode pre --workers 20

# Use 5 workers to reduce database load
python migration_counter.py --mode pre --workers 5
```

Default: 10 workers

### Both Pre & Post in One Run

Count both before and after in a single command:

```bash
python migration_counter.py --mode both --config ~/.migration_config.json
# Generates both pre_migration_count.json AND post_migration_count.json
```

## Error Handling

The scripts handle common errors gracefully:

- **Missing database** — Exits with error message, check credentials
- **Connection refused** — Verify host, port, and firewall rules
- **Permission denied** — Ensure database user has SELECT permission on all tables
- **Missing snapshot file** — Reporter will fail if pre/post files don't exist
- **Config file not found** — Falls back to environment variables or defaults

All errors are printed to stderr with useful context.

## Performance Notes

- **Table counting** uses parallel workers (default 10) for speed
- **Large databases** (1000+ tables): Expect 1-5 minutes depending on database size and network latency
- **Network latency** is the primary bottleneck for remote databases
- **CPU usage** is minimal; I/O bound operation (database queries)

Example timings:
- 50 tables: ~5-10 seconds
- 500 tables: ~30-60 seconds
- 5000 tables: ~2-5 minutes

## Troubleshooting

### Q: Script can't connect to database

**A:** Verify credentials and network connectivity:
```bash
# Test connection manually (requires psql client)
psql -h localhost -U postgres -d postgres -c "SELECT 1"

# Verify credentials in config or environment
echo $DB_HOST $DB_USER $DB_NAME
cat ~/.migration_config.json
```

### Q: Permission denied on certain tables

**A:** The database user needs SELECT permission on all tables:
```sql
-- Grant SELECT on all tables to migration_user
GRANT SELECT ON ALL TABLES IN SCHEMA public TO migration_user;
```

### Q: How do I know if records were lost?

**A:** Look for:
1. 🔴 Red rows in the HTML report (LOST status)
2. Negative "Difference" values in the CSV
3. Critical warning banner at top of HTML report

### Q: Can I run multiple migrations in parallel?

**A:** Yes, save each migration's snapshots to different directories:
```bash
python migration_counter.py --mode pre --output-dir ./migration_v1 ...
python migration_counter.py --mode pre --output-dir ./migration_v2 ...
```

## Requirements

- **Python:** 3.6 or higher
- **psycopg2:** Any recent version (2.8+)
- **PostgreSQL:** 9.6 or higher (any modern version)
- **Network:** Ability to connect to PostgreSQL server
- **Disk:** Minimal (~1 MB per snapshot JSON file, negligible for reports)

## License

Open source - use freely for data migration purposes.

## Support

For issues, questions, or improvements:
1. Verify PostgreSQL connectivity with `psql` command
2. Check error messages in stderr output
3. Ensure database user has proper SELECT permissions
4. Consult PostgreSQL documentation for connection string format

## Summary

This tool simplifies the critical task of validating data integrity during PostgreSQL migrations. By comparing record counts before and after, you can quickly identify potential issues and ensure no data is lost or unexpectedly altered.

Use the HTML report for human review and the CSV for automated analysis or documentation.
