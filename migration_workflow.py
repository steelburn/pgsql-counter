#!/usr/bin/env python3
"""
Convenience wrapper script for complete migration count and reporting workflow.

Usage:
    python migration_workflow.py --config ~/.migration_config.json --output-dir reports
    python migration_workflow.py --mode count-only --host localhost --user postgres
    python migration_workflow.py --mode report-only --pre pre_migration_count.json --post post_migration_count.json
"""

import sys
import argparse
import subprocess
import json
from pathlib import Path


def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"\n{'='*60}")
    print(f"▶ {description}")
    print(f"{'='*60}")
    try:
        result = subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Error: {description} failed", file=sys.stderr)
        return False


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Migration Counter & Reporter Workflow - Count and compare database records"
    )
    parser.add_argument(
        "--mode",
        choices=["full", "count-only", "report-only"],
        default="full",
        help="Workflow mode: 'full' (count + report), 'count-only', or 'report-only'",
    )
    
    # Counter arguments
    parser.add_argument("--host", help="Database host")
    parser.add_argument("--user", help="Database user")
    parser.add_argument("--password", help="Database password")
    parser.add_argument("--database", "--db", help="Database name")
    parser.add_argument("--port", type=int, help="Database port")
    parser.add_argument("--config", help="Config file path")
    
    # Workflow arguments
    parser.add_argument(
        "--output-dir",
        default=".",
        help="Directory for snapshots and reports",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=10,
        help="Parallel workers for table counting",
    )
    
    # Reporter arguments
    parser.add_argument("--pre", help="Pre-migration snapshot file (for report-only mode)")
    parser.add_argument("--post", help="Post-migration snapshot file (for report-only mode)")
    parser.add_argument(
        "--report-output",
        choices=["html", "csv", "both"],
        default="both",
        help="Report format",
    )
    parser.add_argument("--html-file", default="migration_report.html")
    parser.add_argument("--csv-file", default="migration_report.csv")

    return parser.parse_args()


def build_counter_command(args):
    """Build migration_counter.py command."""
    cmd = ["python", "migration_counter.py", "--mode", "both"]
    
    if args.host:
        cmd.extend(["--host", args.host])
    if args.user:
        cmd.extend(["--user", args.user])
    if args.password:
        cmd.extend(["--password", args.password])
    if args.database:
        cmd.extend(["--database", args.database])
    if args.port:
        cmd.extend(["--port", str(args.port)])
    if args.config:
        cmd.extend(["--config", args.config])
    
    cmd.extend(["--output-dir", args.output_dir])
    cmd.extend(["--workers", str(args.workers)])
    
    return cmd


def build_reporter_command(args):
    """Build migration_reporter.py command."""
    pre_file = args.pre or f"{args.output_dir}/pre_migration_count.json"
    post_file = args.post or f"{args.output_dir}/post_migration_count.json"
    
    cmd = [
        "python", "migration_reporter.py",
        "--pre", pre_file,
        "--post", post_file,
        "--output", args.report_output,
        "--output-dir", args.output_dir,
        "--html-file", args.html_file,
        "--csv-file", args.csv_file,
    ]
    
    return cmd


def main():
    args = parse_arguments()
    
    print("╔════════════════════════════════════════════════════════════╗")
    print("║  PostgreSQL Migration Counter & Reporter Workflow         ║")
    print("╚════════════════════════════════════════════════════════════╝")
    
    # Create output directory
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    
    success = True
    
    # Phase 1: Count (if not report-only)
    if args.mode in ["full", "count-only"]:
        cmd = build_counter_command(args)
        if not run_command(cmd, "Running pre and post-migration counts..."):
            success = False
        
        if args.mode == "count-only":
            if success:
                print("\n✓ Record counting completed successfully")
                pre_file = f"{args.output_dir}/pre_migration_count.json"
                post_file = f"{args.output_dir}/post_migration_count.json"
                print(f"  Pre-migration:  {pre_file}")
                print(f"  Post-migration: {post_file}")
            sys.exit(0 if success else 1)
    
    # Phase 2: Report (if not count-only)
    if args.mode in ["full", "report-only"]:
        if success or args.mode == "report-only":  # Allow report-only even if count failed
            cmd = build_reporter_command(args)
            if not run_command(cmd, "Generating comparison reports..."):
                success = False
    
    # Summary
    print(f"\n{'='*60}")
    if success:
        print("✓ Workflow completed successfully!")
        print(f"\nOutput files:")
        print(f"  HTML Report: {args.output_dir}/{args.html_file}")
        print(f"  CSV Report:  {args.output_dir}/{args.csv_file}")
        print(f"\nNext: Open {args.output_dir}/{args.html_file} in your browser to review")
    else:
        print("✗ Workflow failed - check errors above")
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
