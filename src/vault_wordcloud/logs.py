"""Logging setup: timestamped lines to the terminal and to logs/run_<timestamp>.log at the same time.

Global context: one root-logger config shared by every module (each does logging.getLogger(__name__)).
Pattern from the logging cookbook "logging to multiple destinations":
https://docs.python.org/3/howto/logging-cookbook.html#logging-to-multiple-destinations
"""

import logging
import sys
from datetime import datetime
from pathlib import Path


def setup_logging(log_dir: Path) -> Path:
    """Send INFO+ records to stdout and a fresh timestamped file; return that file's path."""
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"run_{datetime.now():%Y%m%d_%H%M%S}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",  # asctime gives the timestamp on every line
        handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler(log_file, encoding="utf-8")],
        force=True,  # replace handlers from an earlier call (e.g. a second run in the same test session)
    )
    return log_file
