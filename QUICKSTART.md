# Quick Start Guide

## Installation (One-time setup)

```bash
cd pgsql-counter
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install psycopg2-binary
```

## Basic Workflow

### Option 1: Full Workflow (Count + Report)

```bash
# Make sure venv is activated
source venv/bin/activate

# Run complete migration workflow
python migration_workflow.py \
  --config ~/.migration_config.json \
  --output-dir migration_reports
```

### Option 2: Manual Two-Step Process

**Step 1: Pre-Migration Count**
```bash
python migration_counter.py --mode pre \
  --host localhost \
  --user postgres \
  --password secretpw \
  --database mydb
```

**Step 2: Run Your Migration**
```bash
# Your migration scripts here
./run_migration.sh
```

**Step 3: Post-Migration Count**
```bash
python migration_counter.py --mode post \
  --host localhost \
  --user postgres \
  --password secretpw \
  --database mydb
```

**Step 4: Generate Report**
```bash
python migration_reporter.py \
  --pre pre_migration_count.json \
  --post post_migration_count.json \
  --output both
```

## Using Config File

Create `~/.migration_config.json`:
```json
{
  "host": "db.company.com",
  "port": 5432,
  "user": "migration_user",
  "password": "your_password",
  "database": "production_db"
}
```

Then use it:
```bash
python migration_counter.py --mode pre --config ~/.migration_config.json
```

## Using Environment Variables

```bash
export DB_HOST=db.company.com
export DB_USER=migration_user
export DB_PASSWORD=your_password
export DB_NAME=production_db

python migration_counter.py --mode pre
```

## Check Results

1. **HTML Report** (Open in browser):
   ```bash
   open migration_report.html  # macOS
   xdg-open migration_report.html  # Linux
   start migration_report.html  # Windows
   ```

2. **CSV Report** (Open in Excel/spreadsheet):
   ```bash
   cat migration_report.csv
   # Or open in your favorite spreadsheet application
   ```

## Common Scenarios

### Scenario 1: Large Database (1000+ tables)
Use more workers for faster counting:
```bash
python migration_counter.py --mode pre --workers 20
```

### Scenario 2: Remote Database
Specify host explicitly:
```bash
python migration_counter.py --mode both \
  --host production-db.aws.com \
  --user postgres \
  --password "$(aws secretsmanager get-secret-value --secret-id db-password | jq -r .SecretString)"
```

### Scenario 3: Count-Only (No Report)
```bash
python migration_workflow.py --mode count-only --config ~/.migration_config.json
```

### Scenario 4: Report-Only (Pre-existing Snapshots)
```bash
python migration_workflow.py --mode report-only \
  --pre old_snapshots/pre_migration_count.json \
  --post old_snapshots/post_migration_count.json
```

## Troubleshooting

### Cannot connect to database
```bash
# Test connection with psql (if available)
psql -h localhost -U postgres -d postgres -c "SELECT 1"

# Check credentials in config
cat ~/.migration_config.json

# Check environment variables
echo $DB_HOST $DB_USER $DB_NAME
```

### Permission denied on tables
The database user needs SELECT access:
```sql
GRANT SELECT ON ALL TABLES IN SCHEMA public TO migration_user;
```

### Reports show "Record Loss" - is this bad?
Not necessarily! Records can be lost due to:
- Data cleanup/deduplication
- Filter migrations
- Intentional data purging

Review the HTML report to see which tables were affected.

## Files Generated

After running, you'll have:
- `pre_migration_count.json` — Snapshot of all table counts before migration
- `post_migration_count.json` — Snapshot of all table counts after migration
- `migration_report.html` — Interactive comparison report
- `migration_report.csv` — Machine-readable comparison

## Next Steps

1. Review `README.md` for detailed documentation
2. Check `migration_report.html` to see detailed comparisons
3. If issues found, investigate specific tables mentioned in report
4. Archive reports for compliance/audit trail

## Getting Help

- Check `README.md` for comprehensive documentation
- Review script help: `python migration_counter.py --help`
- Test with sample data: See README's troubleshooting section
- Check script output for detailed error messages
