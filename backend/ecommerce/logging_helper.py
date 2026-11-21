"""Structured Terminal Logging for SocialPlus.ai E-Commerce Intelligence.

Outputs standardized, timestamped, and stage-specific log lines to both
the console/terminal and Python logging hierarchy without swallowing exceptions.
"""
from __future__ import annotations

import logging
import sys
import traceback
from typing import Any, Optional

logger = logging.getLogger("socialplus.ecommerce")


def log_ecom(stage_message: str, level: str = "INFO", details: Optional[str] = None, exc: Optional[Exception] = None) -> None:
    """Print clean structured terminal output and emit to Python standard logger."""
    lvl = level.upper()
    prefix = f"[{lvl}]"
    line = f"{prefix} {stage_message}"
    if details:
        line += f" — {details}"

    # Print directly to stdout/stderr so terminal users see real-time updates
    stream = sys.stderr if lvl in ("ERROR", "CRITICAL") else sys.stdout
    print(line, file=stream, flush=True)

    # Also log to Python logger
    log_func = getattr(logger, lvl.lower(), logger.info)
    if exc:
        log_func(line, exc_info=exc)
    else:
        log_func(line)


def log_zero_reviews_reason(reason: str, platform: str, url: str) -> None:
    """Log clear terminal diagnostic when zero customer reviews are returned."""
    log_ecom(f"Zero reviews found for {platform.upper()}", level="WARN", details=f"Reason: {reason}")

