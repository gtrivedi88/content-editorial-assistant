"""Reporting service — issue aggregation, scoring, and export formatting."""

from app.services.reporting.builder import build_report
from app.services.reporting.readability import calculate_readability

__all__ = ["build_report", "calculate_readability"]
