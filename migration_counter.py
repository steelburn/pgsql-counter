#!/usr/bin/env python3
"""
PostgreSQL Data Migration Counter Script

Connects to a PostgreSQL database and counts records in all tables.
Outputs snapshot to pre_migration_count.json or post_migration_count.json.

Usage:
    python migration_counter.py --mode pre --host localhost --user postgres --password pw --db mydb
    python migration_counter.py --mode post --config ~/.migration_config.json
    DB_HOST=localhost python migration_counter.py --mode both
"""

import json
import sys
import argparse
import os
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

# Configure logging
logging.basicConfig(
    filename="sql_queries.log",
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
)

logging.basicConfig(
    filename="sql_results.log",
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
)

try:
    import psycopg2
    from psycopg2 import sql
except ImportError:
    print("Error: psycopg2 not installed. Install with: pip install psycopg2-binary", file=sys.stderr)
    sys.exit(1)


class CounterConfig:
    """Parse database connection credentials from CLI args, env vars, or config file."""

    def __init__(self):
        self.host = None
        self.user = None
        self.password = None
        self.database = None
        self.port = 5432

    @staticmethod
    def from_cli_args(args):
        """Create config from command-line arguments."""
        config = CounterConfig()
        config.host = args.host
        config.user = args.user
        config.password = args.password
        config.database = args.database
        if args.port:
            config.port = args.port
        return config

    @staticmethod
    def from_env_vars():
        """Create config from environment variables."""
        config = CounterConfig()
        config.host = os.getenv("DB_HOST", "localhost")
        config.user = os.getenv("DB_USER", "postgres")
        config.password = os.getenv("DB_PASSWORD", "")
        config.database = os.getenv("DB_NAME", "postgres")
        port = os.getenv("DB_PORT")
        if port:
            config.port = int(port)
        return config

    @staticmethod
    def from_config_file(filepath):
        """Create config from JSON config file."""
        try:
            with open(filepath, "r") as f:
                data = json.load(f)
            config = CounterConfig()
            config.host = data.get("host", "localhost")
            config.user = data.get("user", "postgres")
            config.password = data.get("password", "")
            config.database = data.get("database", "postgres")
            config.port = data.get("port", 5432)
            return config
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error reading config file {filepath}: {e}", file=sys.stderr)
            return None

    def validate(self):
        """Check that required fields are set."""
        if not all([self.host, self.user, self.database]):
            print("Error: Missing required database credentials (host, user, database)", file=sys.stderr)
            return False
        return True

    def to_dict(self):
        """Return config as dictionary (for logging, excludes password)."""
        return {
            "host": self.host,
            "port": self.port,
            "user": self.user,
            "database": self.database,
        }


class PostgreSQLCounter:
    """Connects to PostgreSQL and counts records in all tables."""

    def __init__(self, config):
        self.config = config
        self.conn = None
        self.schema = "public"  # Default schema

    def connect(self):
        """Establish connection to PostgreSQL database."""
        try:
            self.conn = psycopg2.connect(
                host=self.config.host,
                port=self.config.port,
                user=self.config.user,
                password=self.config.password,
                database=self.config.database,
            )
            print(f"Connected to {self.config.database} at {self.config.host}:{self.config.port}")
            return True
        except psycopg2.Error as e:
            print(f"Error connecting to database: {e}", file=sys.stderr)
            return False

    def disconnect(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            print("Disconnected from database")

    def get_all_tables(self):
        """
        Query information_schema to get all user-defined tables.
        Excludes system tables (pg_catalog, information_schema).
        """
        if not self.conn:
            return []

        try:
            cursor = self.conn.cursor()
            query = """
            SELECT table_schema, table_name
            FROM information_schema.tables
            WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
            AND table_type = 'BASE TABLE'
            ORDER BY table_schema, table_name
            """
            cursor.execute(query)
            tables = [(row[0], row[1]) for row in cursor.fetchall()]
            cursor.close()
            return tables
        except psycopg2.Error as e:
            print(f"Error querying tables: {e}", file=sys.stderr)
            return []

    def count_records(self, schema, table_name):
        """
        Count records in a single table.
        Returns tuple (schema.table_name, count) or None on error.
        """
        if not self.conn:
            return None

        try:
            cursor = self.conn.cursor()
            query = sql.SQL("SELECT COUNT(*) FROM {}.{}").format(
                sql.Identifier(schema),
                sql.Identifier(table_name),
            )
            logging.info(f"Executing query: {query.as_string(self.conn)}")
            cursor.execute(query)
            count = cursor.fetchone()[0]
            logging.info(f"Query result for {schema}.{table_name}: {count}")
            cursor.close()
            return (f"{schema}.{table_name}", count)
        except psycopg2.Error as e:
            logging.error(f"Error executing query for {schema}.{table_name}: {e}")
            print(f"Error counting records in {schema}.{table_name}: {e}", file=sys.stderr)
            return None

    def generate_count_snapshot(self, max_workers=10):
        """
        Generate a snapshot of record counts for all tables.
        Uses ThreadPoolExecutor for parallel table counting.
        Returns dict: {schema.table_name: count, ...} or None on error.
        """
        if not self.conn:
            print("Error: Not connected to database", file=sys.stderr)
            return None

        tables = self.get_all_tables()
        if not tables:
            print("No tables found in database", file=sys.stderr)
            return {}

        snapshot = {}
        failed_tables = []

        print(f"Counting records in {len(tables)} tables using {max_workers} workers...")

        # Use ThreadPoolExecutor for parallel counting
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self.count_records, schema, table): (schema, table)
                for schema, table in tables
            }

            for future in as_completed(futures):
                result = future.result()
                if result:
                    table_full_name, count = result
                    snapshot[table_full_name] = count
                    print(f"  {table_full_name}: {count} rows")
                else:
                    schema, table = futures[future]
                    failed_tables.append(f"{schema}.{table}")

        if failed_tables:
            print(f"Warning: Failed to count {len(failed_tables)} tables: {', '.join(failed_tables)}", file=sys.stderr)

        return snapshot

    def to_dict(self):
        """Return config info for snapshot metadata."""
        return self.config.to_dict()


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="PostgreSQL Data Migration Counter - Count records before/after migration"
    )
    parser.add_argument(
        "--mode",
        choices=["pre", "post", "both"],
        required=True,
        help="Migration phase: 'pre' (before), 'post' (after), or 'both'",
    )
    parser.add_argument(
        "--host",
        help="Database host (default: from env DB_HOST or config)",
    )
    parser.add_argument(
        "--user",
        help="Database user (default: from env DB_USER or config)",
    )
    parser.add_argument(
        "--password",
        help="Database password (default: from env DB_PASSWORD or config)",
    )
    parser.add_argument(
        "--database",
        "--db",
        help="Database name (default: from env DB_NAME or config)",
    )
    parser.add_argument(
        "--port",
        type=int,
        help="Database port (default: 5432)",
    )
    parser.add_argument(
        "--config",
        help="Path to JSON config file (default: ~/.migration_config.json)",
    )
    parser.add_argument(
        "--output-dir",
        default=".",
        help="Directory to save count files (default: current directory)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=10,
        help="Number of parallel workers for table counting (default: 10)",
    )

    return parser.parse_args()


def load_config_with_priority(args):
    """
    Load config with priority: CLI args > env vars > config file > defaults.
    """
    config = None

    # Try config file first
    config_file = args.config or os.path.expanduser("~/.migration_config.json")
    if os.path.exists(config_file):
        config = CounterConfig.from_config_file(config_file)
        if config:
            print(f"Loaded config from {config_file}")

    # Overlay environment variables
    env_config = CounterConfig.from_env_vars()
    if not config:
        config = env_config
    else:
        # Merge: env vars override config file if set
        if os.getenv("DB_HOST"):
            config.host = env_config.host
        if os.getenv("DB_USER"):
            config.user = env_config.user
        if os.getenv("DB_PASSWORD"):
            config.password = env_config.password
        if os.getenv("DB_NAME"):
            config.database = env_config.database
        if os.getenv("DB_PORT"):
            config.port = env_config.port

    # Overlay CLI arguments (highest priority)
    if args.host:
        config.host = args.host
    if args.user:
        config.user = args.user
    if args.password:
        config.password = args.password
    if args.database:
        config.database = args.database
    if args.port:
        config.port = args.port

    return config


def save_snapshot(snapshot, mode, output_dir):
    """Save snapshot to JSON file with timestamp and metadata."""
    timestamp = datetime.now().isoformat()
    output_data = {
        "timestamp": timestamp,
        "mode": mode,
        "tables": snapshot,
        "total_records": sum(snapshot.values()) if snapshot else 0,
        "table_count": len(snapshot),
    }

    filename_map = {"pre": "pre_migration_count.json", "post": "post_migration_count.json"}
    filename = filename_map.get(mode, f"migration_count_{mode}.json")
    filepath = os.path.join(output_dir, filename)

    try:
        with open(filepath, "w") as f:
            json.dump(output_data, f, indent=2)
        print(f"\nSnapshot saved to {filepath}")
        print(f"  Total records: {output_data['total_records']}")
        print(f"  Total tables: {output_data['table_count']}")
        return True
    except IOError as e:
        print(f"Error saving snapshot: {e}", file=sys.stderr)
        return False


def main():
    args = parse_arguments()

    # Ensure output directory exists
    os.makedirs(args.output_dir, exist_ok=True)

    # Load configuration with priority
    config = load_config_with_priority(args)
    if not config or not config.validate():
        print("Error: Could not load valid database configuration", file=sys.stderr)
        sys.exit(1)

    print(f"Database config: {config.to_dict()}")

    # Process based on mode
    modes = [args.mode] if args.mode != "both" else ["pre", "post"]

    all_success = True
    for mode in modes:
        print(f"\n--- Running {mode}-migration count ---")

        counter = PostgreSQLCounter(config)
        if not counter.connect():
            all_success = False
            continue

        snapshot = counter.generate_count_snapshot(max_workers=args.workers)
        counter.disconnect()

        if snapshot is not None:
            if not save_snapshot(snapshot, mode, args.output_dir):
                all_success = False
        else:
            all_success = False

    if all_success:
        print("\n✓ All snapshots generated successfully")
        sys.exit(0)
    else:
        print("\n✗ Some snapshots failed to generate", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
