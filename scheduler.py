#!/usr/bin/env python3
"""
Local Scheduler — Spotify Review Discovery Pipeline
=====================================================
Runs the complete data refresh pipeline locally on a schedule or once.

Usage:
    # Run once immediately:
    python scheduler.py --once

    # Run on a schedule (default: every 24 hours):
    python scheduler.py

    # Custom interval (in seconds):
    python scheduler.py --interval 3600
"""

import os
import sys
import time
import argparse
import subprocess
import logging
from datetime import datetime

# ── Logging Setup ────────────────────────────────────────────────────────────
# Use UTF-8 on the stream handler to avoid Windows CP1252 encoding errors
_stream_handler = logging.StreamHandler(sys.stdout)
_stream_handler.stream = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        _stream_handler,
        logging.FileHandler("data/scheduler.log", mode="a", encoding="utf-8"),
    ],
)
log = logging.getLogger("scheduler")

# ── Configuration ────────────────────────────────────────────────────────────
DEFAULT_INTERVAL_SECONDS = 24 * 60 * 60  # 24 hours

PIPELINE_STEPS = [
    {
        "name": "Step 1 -- Ingest Reviews",
        "description": "Scrape App Store, Play Store, and generate social mocks",
        "cmd": [
            sys.executable, "src/phase1/ingest_reviews.py",
            "--limit-scraped", "500",
            "--limit-mocked", "500",
        ],
    },
    {
        "name": "Step 2 -- Analyze Reviews",
        "description": "Run sentiment + topic analysis (LLM or rules-based fallback)",
        "cmd": [sys.executable, "src/phase1/analyze_reviews.py"],
    },
    {
        "name": "Step 3 -- Seed Track Catalog",
        "description": "Rebuild ChromaDB vector embeddings for semantic track search",
        "cmd": [sys.executable, "src/phase4/seed_tracks.py"],
    },
]


def run_step(step: dict) -> bool:
    """Execute a single pipeline step. Returns True on success, False on failure."""
    log.info("-" * 60)
    log.info(f">> {step['name']}")
    log.info(f"   {step['description']}")
    log.info(f"   Command: {' '.join(step['cmd'])}")

    start = time.time()
    try:
        result = subprocess.run(
            step["cmd"],
            capture_output=True,
            text=True,
            cwd=os.path.abspath(os.path.dirname(__file__)),
            timeout=300,  # 5-minute timeout per step
        )
        elapsed = time.time() - start

        if result.returncode == 0:
            log.info(f"   [PASS] Completed in {elapsed:.1f}s")
            if result.stdout.strip():
                for line in result.stdout.strip().splitlines()[-10:]:  # last 10 lines
                    log.info(f"     {line}")
            return True
        else:
            log.error(f"   [FAIL] Exit code {result.returncode} in {elapsed:.1f}s")
            if result.stderr.strip():
                for line in result.stderr.strip().splitlines()[-20:]:
                    log.error(f"     {line}")
            return False

    except subprocess.TimeoutExpired:
        log.error("   [FAIL] Timed out after 300s")
        return False
    except FileNotFoundError as e:
        log.error(f"   [FAIL] Script not found: {e}")
        return False
    except Exception as e:
        log.error(f"   [FAIL] Unexpected error: {e}")
        return False


def run_pipeline() -> dict:
    """Run the full pipeline. Returns a summary dict."""
    log.info("=" * 60)
    log.info(f"PIPELINE RUN STARTED -- {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log.info("=" * 60)

    results = {}
    overall_start = time.time()

    for step in PIPELINE_STEPS:
        success = run_step(step)
        results[step["name"]] = "[PASS]" if success else "[FAIL]"
        if not success:
            log.warning("   Step failed -- continuing with next step...")

    total_elapsed = time.time() - overall_start

    log.info("=" * 60)
    log.info(f"PIPELINE SUMMARY (total: {total_elapsed:.1f}s)")
    log.info("=" * 60)
    for step_name, status in results.items():
        log.info(f"  {status}  {step_name}")

    passed = sum(1 for v in results.values() if "PASS" in v)
    log.info(f"\n  {passed}/{len(PIPELINE_STEPS)} steps passed")
    log.info("=" * 60)

    return results


def main():
    parser = argparse.ArgumentParser(description="Spotify Review Discovery — Local Scheduler")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run the pipeline once and exit (no loop)",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=DEFAULT_INTERVAL_SECONDS,
        help=f"Interval in seconds between runs (default: {DEFAULT_INTERVAL_SECONDS})",
    )
    args = parser.parse_args()

    # Ensure log directory exists
    os.makedirs("data", exist_ok=True)

    if args.once:
        log.info("Running pipeline once (--once mode)")
        run_pipeline()
        sys.exit(0)

    # Continuous scheduler loop
    log.info(f"Scheduler started -- running every {args.interval}s ({args.interval/3600:.1f}h)")
    log.info("Press Ctrl+C to stop")

    run_count = 0
    while True:
        run_count += 1
        log.info(f"\nScheduled run #{run_count}")
        run_pipeline()

        next_run = datetime.fromtimestamp(time.time() + args.interval)
        log.info(f"\nNext run at: {next_run.strftime('%Y-%m-%d %H:%M:%S')} (sleeping {args.interval}s)\n")
        try:
            time.sleep(args.interval)
        except KeyboardInterrupt:
            log.info("\nScheduler stopped by user (Ctrl+C)")
            sys.exit(0)


if __name__ == "__main__":
    main()
