# Testing Guide

This guide explains how to use the Docker PostgreSQL test container to validate the migration counter and reporter scripts.

## Prerequisites

- Docker and Docker Compose installed
- Python 3.6+ with virtual environment activated
- `psycopg2-binary` installed (see QUICKSTART.md)

## Starting the Test Container

### Option 1: Using Docker Compose (Recommended)

```bash
cd /home/steelburn/development/pgsql-counter

# Start the PostgreSQL container
docker-compose up -d

# Wait for the container to be healthy (check logs)
docker-compose logs postgres

# You should see: "PostgreSQL init process complete; ready for start up."
```

### Option 2: Check Container Status

```bash
# List running containers
docker-compose ps

# View logs
docker-compose logs -f postgres

# Check health
docker inspect pgsql-counter-test | grep -A 5 '"Health"'
```

## Test Data Overview

The test container includes realistic test data across 13 tables:

| Table | Records | Purpose |
|-------|---------|---------|
| users | 500 | User accounts |
| products | 50 | Product catalog |
| orders | 200 | Customer orders |
| order_items | ~1,500 | Order line items (variable) |
| inventory | 50 | Warehouse inventory |
| reviews | 800 | Product reviews |
| activity_logs | 5,000 | System activity log |
| audit_trail | 3,000 | Audit trail entries |
| sessions | 1,000 | Active sessions |
| payment_methods | 1,200 | Payment methods |
| notifications | 2,000 | User notifications |
| coupons | 5 | Discount coupons |
| categories | 8 | Product categories |
| **TOTAL** | **~18,808** | **All tables** |

## Running Tests

### Test 1: Pre-Migration Count

```bash
# Activate virtual environment
source venv/bin/activate

# Run pre-migration count
python migration_counter.py --mode pre \
  --host localhost \
  --port 5432 \
  --user testuser \
  --password testpass \
  --database test_migration \
  --output-dir test_reports

# Check output
cat test_reports/pre_migration_count.json | python -m json.tool
```

Expected output: JSON file with all 13 tables and their record counts (~18,808 total).

### Test 2: Simulate Migration (Data Change)

Simulate some data changes to test the comparison logic:

```bash
# Connect to database
docker exec -it pgsql-counter-test psql -U testuser -d test_migration

# Inside psql:
-- Delete some records from orders
DELETE FROM public.order_items WHERE id > 1200;
DELETE FROM public.orders WHERE id > 150;

-- Add new records to notifications
INSERT INTO public.notifications (user_id, type, title, message, is_read)
SELECT 
    ((seq % 500) + 1),
    'test',
    'New notification ' || seq::text,
    'Test message',
    false
FROM GENERATE_SERIES(2001, 2500) seq;

-- Exit psql
\q
```

### Test 3: Post-Migration Count

```bash
# Run post-migration count
python migration_counter.py --mode post \
  --host localhost \
  --port 5432 \
  --user testuser \
  --password testpass \
  --database test_migration \
  --output-dir test_reports

# Verify changes were detected
cat test_reports/post_migration_count.json | python -m json.tool
```

### Test 4: Generate Comparison Report

```bash
# Generate HTML and CSV reports
python migration_reporter.py \
  --pre test_reports/pre_migration_count.json \
  --post test_reports/post_migration_count.json \
  --output both \
  --output-dir test_reports

# View results
ls -lh test_reports/
```

Expected output:
- Report shows record loss in `order_items` and `orders` tables
- Report shows record increase in `notifications` table
- HTML report displays critical warning about record loss

### Test 5: Full Workflow Test

```bash
# Complete workflow using convenience script
python migration_workflow.py \
  --host localhost \
  --port 5432 \
  --user testuser \
  --password testpass \
  --database test_migration \
  --output-dir test_reports \
  --mode full

# Review both files
ls -lh test_reports/
```

### Test 6: Test Configuration Priority

Test that CLI args override environment variables and config file:

```bash
# Create a test config
cat > test_config.json << 'EOF'
{
  "host": "wrong-host.com",
  "port": 9999,
  "user": "wronguser",
  "password": "wrongpass",
  "database": "wrongdb"
}
EOF

# CLI args should override config file
python migration_counter.py --mode pre \
  --config test_config.json \
  --host localhost \
  --user testuser \
  --password testpass \
  --database test_migration \
  --output-dir test_reports

# Should succeed (CLI args win)
```

### Test 7: Test Environment Variables

```bash
# Set environment variables
export DB_HOST=localhost
export DB_USER=testuser
export DB_PASSWORD=testpass
export DB_NAME=test_migration
export DB_PORT=5432

# Should work with just environment variables
python migration_counter.py --mode pre --output-dir test_reports

# Unset variables
unset DB_HOST DB_USER DB_PASSWORD DB_NAME DB_PORT
```

## Stopping the Container

### Clean Stop

```bash
# Stop the container
docker-compose stop

# View that it's stopped
docker-compose ps
```

### Full Cleanup (Remove Container and Volume)

```bash
# Remove container and named volumes
docker-compose down -v

# Verify removal
docker-compose ps
docker volume ls
```

### Quick Restart

```bash
# Stop and start again (keeps data)
docker-compose restart

# Or stop and start separately
docker-compose stop
docker-compose start
```

## Advanced Testing

### Test 7: High-Load Test (1M+ Records)

To test with more data, modify `test-data.sql`:

```sql
-- In test-data.sql, increase activity logs
INSERT INTO public.activity_logs (user_id, action, table_name, record_id, new_values)
SELECT 
    ((seq % 500) + 1),
    ...
FROM GENERATE_SERIES(1, 100000) seq;  -- Increase from 5000
```

Then rebuild:
```bash
docker-compose down -v
docker-compose up -d
```

### Test 8: Parallel Workers Test

Test the parallel counting feature:

```bash
# Default workers (10)
time python migration_counter.py --mode pre --workers 10 --host localhost --user testuser --password testpass --database test_migration

# More workers (20)
time python migration_counter.py --mode pre --workers 20 --host localhost --user testuser --password testpass --database test_migration

# Fewer workers (5)
time python migration_counter.py --mode pre --workers 5 --host localhost --user testuser --password testpass --database test_migration

# Compare execution times
```

### Test 9: Connection Failure Test

Test error handling:

```bash
# Wrong password
python migration_counter.py --mode pre \
  --host localhost \
  --user testuser \
  --password wrongpass \
  --database test_migration

# Should fail with: "password authentication failed"

# Wrong database
python migration_counter.py --mode pre \
  --host localhost \
  --user testuser \
  --password testpass \
  --database nonexistent

# Should fail with: "database 'nonexistent' does not exist"

# Wrong host
python migration_counter.py --mode pre \
  --host nonexistent.local \
  --user testuser \
  --password testpass \
  --database test_migration

# Should fail with: "could not translate host name"
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs for errors
docker-compose logs postgres

# Look for initialization errors or port conflicts
# Port 5432 might be in use - change in docker-compose.yml
```

### Container Exits Immediately

```bash
# Check logs
docker-compose logs postgres

# Common causes:
# - Port 5432 already in use
# - Insufficient disk space
# - Permission issues

# Solution: Change port in docker-compose.yml
# ports:
#   - "5433:5432"  # Use 5433 instead
```

### Can't Connect from Script

```bash
# Verify container is running
docker-compose ps

# Test connection manually
docker exec -it pgsql-counter-test psql -U testuser -d test_migration -c "SELECT COUNT(*) FROM public.users;"

# If manual connection works, check Python connection
python -c "import psycopg2; psycopg2.connect('host=localhost user=testuser password=testpass database=test_migration')"
```

### Permission Denied on File

```bash
# If you see permission errors, rebuild
docker-compose down -v
docker system prune -a
docker-compose up -d
```

## Quick Reference Commands

```bash
# Start container
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f postgres

# Connect to database
docker exec -it pgsql-counter-test psql -U testuser -d test_migration

# Run migration count
python migration_counter.py --mode pre --host localhost --user testuser --password testpass --database test_migration

# Generate report
python migration_reporter.py --pre pre_migration_count.json --post post_migration_count.json

# Stop container
docker-compose stop

# Remove everything
docker-compose down -v
```

## Test Checklist

Use this checklist to validate the complete testing workflow:

- [ ] Docker container starts without errors
- [ ] Pre-migration count generates 13 tables with ~18,808 records
- [ ] Can simulate data changes via `psql`
- [ ] Post-migration count detects record changes
- [ ] HTML report generates with proper styling
- [ ] CSV report generates with correct format
- [ ] Critical warnings appear for record loss
- [ ] Configuration priority works (CLI > env > config)
- [ ] Environment variables are properly read
- [ ] Parallel workers improve speed
- [ ] Error handling works for invalid connections
- [ ] All cleanup commands work without errors

## Next Steps

After successful testing with this container:

1. **Test against real PostgreSQL** — Use actual database connection string
2. **Archive test reports** — Save HTML/CSV for comparison
3. **Document findings** — Note any discrepancies or issues
4. **Scale testing** — Test with larger production-like datasets
5. **Production run** — Run against actual migration before/after

## Support

For issues:
1. Check Docker logs: `docker-compose logs postgres`
2. Verify psycopg2 connection: `python -c "import psycopg2; print('OK')"`
3. Test psql directly: `docker exec ... psql`
4. Review error messages for specific guidance
