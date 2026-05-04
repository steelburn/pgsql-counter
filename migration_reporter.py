#!/usr/bin/env python3
"""
PostgreSQL Data Migration Report Generator

Compares pre and post-migration snapshots and generates HTML/CSV reports
highlighting record discrepancies.

Usage:
    python migration_reporter.py --pre pre_migration_count.json --post post_migration_count.json --output html
    python migration_reporter.py --pre pre_migration_count.json --post post_migration_count.json --output csv
"""

import json
import sys
import csv
import argparse
from pathlib import Path
from datetime import datetime


class CounterComparator:
    """Compare two migration count snapshots and identify discrepancies."""

    def __init__(self, pre_snapshot, post_snapshot):
        self.pre_snapshot = pre_snapshot
        self.post_snapshot = post_snapshot
        self.comparison = []

    def load_snapshot(self, filepath):
        """Load a snapshot JSON file."""
        try:
            with open(filepath, "r") as f:
                data = json.load(f)
            return data
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading snapshot {filepath}: {e}", file=sys.stderr)
            return None

    def generate_comparison(self):
        """
        Generate comparison data.
        Returns list of dicts: {table, pre_count, post_count, difference, status}
        """
        if not self.pre_snapshot or not self.post_snapshot:
            return []

        pre_tables = self.pre_snapshot.get("tables", {})
        post_tables = self.post_snapshot.get("tables", {})

        # Get all unique tables
        all_tables = set(pre_tables.keys()) | set(post_tables.keys())

        comparison = []

        for table in sorted(all_tables):
            pre_count = pre_tables.get(table, 0)
            post_count = post_tables.get(table, 0)
            difference = post_count - pre_count

            # Determine status
            if pre_count == post_count:
                status = "MATCH"
            elif post_count > pre_count:
                status = "INCREASED"
            elif post_count < pre_count:
                status = "LOST"
            else:
                status = "UNKNOWN"

            # Mark as critical if records were lost
            is_critical = post_count < pre_count

            comparison.append({
                "table": table,
                "pre_count": pre_count,
                "post_count": post_count,
                "difference": difference,
                "status": status,
                "is_critical": is_critical,
            })

        self.comparison = comparison
        return comparison

    def get_summary(self):
        """Generate summary statistics."""
        if not self.comparison:
            return None

        total_tables = len(self.comparison)
        total_pre = sum(row["pre_count"] for row in self.comparison)
        total_post = sum(row["post_count"] for row in self.comparison)
        total_difference = total_post - total_pre

        matched = len([r for r in self.comparison if r["status"] == "MATCH"])
        increased = len([r for r in self.comparison if r["status"] == "INCREASED"])
        lost = len([r for r in self.comparison if r["status"] == "LOST"])

        return {
            "total_tables": total_tables,
            "total_pre_records": total_pre,
            "total_post_records": total_post,
            "total_difference": total_difference,
            "matched_tables": matched,
            "increased_tables": increased,
            "lost_records_tables": lost,
        }


class HTMLReporter:
    """Generate HTML report from comparison data."""

    @staticmethod
    def generate_html(comparison, summary, pre_timestamp, post_timestamp):
        """Generate HTML report as string."""
        html_parts = []

        # HTML header
        html_parts.append("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Migration Report</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            border-bottom: 3px solid #007bff;
            padding-bottom: 10px;
        }
        h2 {
            color: #555;
            margin-top: 30px;
        }
        .summary-box {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }
        .summary-item {
            background-color: #f9f9f9;
            padding: 15px;
            border-left: 4px solid #007bff;
            border-radius: 3px;
        }
        .summary-item label {
            font-weight: bold;
            color: #666;
            display: block;
            font-size: 0.9em;
        }
        .summary-item .value {
            font-size: 1.5em;
            color: #333;
            margin-top: 5px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        th {
            background-color: #007bff;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: bold;
        }
        td {
            padding: 10px 12px;
            border-bottom: 1px solid #ddd;
        }
        tr:nth-child(even) {
            background-color: #f9f9f9;
        }
        tr:hover {
            background-color: #f0f0f0;
        }
        .match {
            background-color: #d4edda;
            font-weight: bold;
        }
        .increased {
            background-color: #fff3cd;
        }
        .lost {
            background-color: #f8d7da;
            font-weight: bold;
        }
        .positive {
            color: #28a745;
        }
        .negative {
            color: #dc3545;
        }
        .neutral {
            color: #666;
        }
        .footer {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            font-size: 0.9em;
            color: #666;
        }
        .critical-warning {
            background-color: #f8d7da;
            border: 1px solid #f5c6cb;
            color: #721c24;
            padding: 15px;
            border-radius: 4px;
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>PostgreSQL Migration Report</h1>
""")

        # Add critical warning if there are lost records
        if summary["lost_records_tables"] > 0:
            html_parts.append(f"""        <div class="critical-warning">
            <strong>⚠️ WARNING: Record Loss Detected!</strong><br>
            {summary['lost_records_tables']} table(s) have fewer records after migration.
            Total records lost: <strong>{abs(min(0, summary['total_difference']))}</strong>
        </div>
""")

        # Summary section
        html_parts.append("        <h2>Summary</h2>\n        <div class=\"summary-box\">\n")
        html_parts.append(f"""            <div class="summary-item">
                <label>Pre-Migration Records</label>
                <div class="value">{summary['total_pre_records']:,}</div>
            </div>
            <div class="summary-item">
                <label>Post-Migration Records</label>
                <div class="value">{summary['total_post_records']:,}</div>
            </div>
            <div class="summary-item">
                <label>Net Change</label>
                <div class="value {'positive' if summary['total_difference'] >= 0 else 'negative'}">{summary['total_difference']:+,}</div>
            </div>
            <div class="summary-item">
                <label>Total Tables</label>
                <div class="value">{summary['total_tables']}</div>
            </div>
            <div class="summary-item">
                <label>Matched Tables</label>
                <div class="value positive">{summary['matched_tables']}</div>
            </div>
            <div class="summary-item">
                <label>Increased Tables</label>
                <div class="value neutral">{summary['increased_tables']}</div>
            </div>
            <div class="summary-item">
                <label>Lost Data Tables</label>
                <div class="value negative">{summary['lost_records_tables']}</div>
            </div>
        </div>
""")

        # Detailed comparison table
        html_parts.append("        <h2>Detailed Comparison</h2>\n")
        html_parts.append("""        <table>
            <thead>
                <tr>
                    <th>Table Name</th>
                    <th>Pre-Migration</th>
                    <th>Post-Migration</th>
                    <th>Difference</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
""")

        for row in comparison:
            status_class = row["status"].lower()
            diff_class = "positive" if row["difference"] >= 0 else "negative"
            html_parts.append(f"""                <tr class="{status_class}">
                    <td>{row['table']}</td>
                    <td>{row['pre_count']:,}</td>
                    <td>{row['post_count']:,}</td>
                    <td class="{diff_class}">{row['difference']:+,}</td>
                    <td>{row['status']}</td>
                </tr>
""")

        html_parts.append("""            </tbody>
        </table>
""")

        # Footer with metadata
        html_parts.append(f"""        <div class="footer">
            <p><strong>Report Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>Pre-Migration Snapshot:</strong> {pre_timestamp}</p>
            <p><strong>Post-Migration Snapshot:</strong> {post_timestamp}</p>
        </div>
    </div>
</body>
</html>
""")

        return "\n".join(html_parts)

    @staticmethod
    def save_html(html_content, filepath):
        """Save HTML report to file."""
        try:
            with open(filepath, "w") as f:
                f.write(html_content)
            print(f"HTML report saved to {filepath}")
            return True
        except IOError as e:
            print(f"Error saving HTML report: {e}", file=sys.stderr)
            return False


class CSVReporter:
    """Generate CSV report from comparison data."""

    @staticmethod
    def generate_csv_rows(comparison, summary):
        """Generate CSV rows including summary."""
        rows = []

        # Summary section as CSV comments
        rows.append(["# Migration Comparison Report"])
        rows.append(["# Generated", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
        rows.append(["#"])
        rows.append(["# Summary"])
        rows.append(["# Total Tables", summary["total_tables"]])
        rows.append(["# Pre-Migration Total Records", summary["total_pre_records"]])
        rows.append(["# Post-Migration Total Records", summary["total_post_records"]])
        rows.append(["# Net Change", summary["total_difference"]])
        rows.append(["# Matched Tables", summary["matched_tables"]])
        rows.append(["# Increased Tables", summary["increased_tables"]])
        rows.append(["# Tables with Record Loss", summary["lost_records_tables"]])
        rows.append(["#"])
        rows.append(["# Detailed Comparison"])

        # Header
        rows.append(["Table Name", "Pre-Migration", "Post-Migration", "Difference", "Status"])

        # Detail rows
        for row in comparison:
            rows.append([
                row["table"],
                row["pre_count"],
                row["post_count"],
                row["difference"],
                row["status"],
            ])

        return rows

    @staticmethod
    def save_csv(rows, filepath):
        """Save CSV report to file."""
        try:
            with open(filepath, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerows(rows)
            print(f"CSV report saved to {filepath}")
            return True
        except IOError as e:
            print(f"Error saving CSV report: {e}", file=sys.stderr)
            return False


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="PostgreSQL Migration Report Generator - Compare pre and post-migration snapshots"
    )
    parser.add_argument(
        "--pre",
        required=True,
        help="Path to pre-migration count JSON file",
    )
    parser.add_argument(
        "--post",
        required=True,
        help="Path to post-migration count JSON file",
    )
    parser.add_argument(
        "--output",
        choices=["html", "csv", "both"],
        default="both",
        help="Output format (default: both)",
    )
    parser.add_argument(
        "--output-dir",
        default=".",
        help="Directory to save report files (default: current directory)",
    )
    parser.add_argument(
        "--html-file",
        default="migration_report.html",
        help="HTML report filename (default: migration_report.html)",
    )
    parser.add_argument(
        "--csv-file",
        default="migration_report.csv",
        help="CSV report filename (default: migration_report.csv)",
    )

    return parser.parse_args()


def main():
    args = parse_arguments()

    # Ensure output directory exists
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)

    # Load snapshots
    comparator = CounterComparator(None, None)
    pre_data = comparator.load_snapshot(args.pre)
    post_data = comparator.load_snapshot(args.post)

    if not pre_data or not post_data:
        print("Error: Could not load both snapshot files", file=sys.stderr)
        sys.exit(1)

    # Initialize comparator with loaded data
    comparator.pre_snapshot = pre_data
    comparator.post_snapshot = post_data

    # Generate comparison
    comparison = comparator.generate_comparison()
    summary = comparator.get_summary()

    if not comparison or not summary:
        print("Error: Could not generate comparison", file=sys.stderr)
        sys.exit(1)

    print(f"\nComparison Results:")
    print(f"  Total tables: {summary['total_tables']}")
    print(f"  Pre-migration total: {summary['total_pre_records']:,}")
    print(f"  Post-migration total: {summary['total_post_records']:,}")
    print(f"  Net change: {summary['total_difference']:+,}")
    print(f"  Matched: {summary['matched_tables']}")
    print(f"  Increased: {summary['increased_tables']}")
    print(f"  Record loss: {summary['lost_records_tables']} tables")

    # Generate HTML report
    if args.output in ["html", "both"]:
        html_content = HTMLReporter.generate_html(
            comparison,
            summary,
            pre_data.get("timestamp", "N/A"),
            post_data.get("timestamp", "N/A"),
        )
        html_filepath = f"{args.output_dir}/{args.html_file}"
        if not HTMLReporter.save_html(html_content, html_filepath):
            sys.exit(1)

    # Generate CSV report
    if args.output in ["csv", "both"]:
        csv_rows = CSVReporter.generate_csv_rows(comparison, summary)
        csv_filepath = f"{args.output_dir}/{args.csv_file}"
        if not CSVReporter.save_csv(csv_rows, csv_filepath):
            sys.exit(1)

    print("\n✓ Report(s) generated successfully")
    sys.exit(0)


if __name__ == "__main__":
    main()
