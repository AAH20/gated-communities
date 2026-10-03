"""Moderation Analytics Agent for Gated Communities.

Provides metrics collection and trend analysis for community moderation
activities, including report volumes, resolution times, action breakdowns,
and moderator performance indicators.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any


class Period(str, Enum):
    """Supported analysis periods."""

    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"


class ReportCategory(str, Enum):
    """Categories of moderation reports."""

    SPAM = "spam"
    HARASSMENT = "harassment"
    HATE_SPEECH = "hate_speech"
    MISINFORMATION = "misinformation"
    NSFW = "nsfw"
    IMPERSONATION = "impersonation"
    OTHER = "other"


class ModerationAction(str, Enum):
    """Actions taken by moderators."""

    WARNING = "warning"
    TEMPORARY_MUTE = "temporary_mute"
    TEMPORARY_BAN = "temporary_ban"
    PERMANENT_BAN = "permanent_ban"
    CONTENT_REMOVAL = "content_removal"
    NO_ACTION = "no_action"


@dataclass
class ModerationMetrics:
    """Container for moderation metrics over a given period."""

    period: str
    start_date: str
    end_date: str
    total_reports: int
    resolved_reports: int
    pending_reports: int
    avg_resolution_hours: float
    reports_by_category: dict[str, int]
    actions_taken: dict[str, int]
    moderator_count: int
    escalation_rate: float
    false_positive_rate: float
    community_satisfaction: float
    peak_report_hour: int
    repeat_offender_rate: float


@dataclass
class TrendAnalysis:
    """Container for trend analysis results."""

    period: str
    start_date: str
    end_date: str
    report_volume_change_pct: float
    resolution_time_change_pct: float
    escalation_rate_change_pct: float
    satisfaction_change_pct: float
    top_growing_category: str
    top_declining_category: str
    anomaly_detected: bool
    anomaly_description: str | None
    recommendations: list[str] = field(default_factory=list)


def _get_period_dates(period: str) -> tuple[datetime, datetime]:
    """Calculate start and end dates for the given period."""
    end = datetime.now()
    if period == Period.DAY.value:
        start = end - timedelta(days=1)
    elif period == Period.WEEK.value:
        start = end - timedelta(weeks=1)
    elif period == Period.MONTH.value:
        start = end - timedelta(days=30)
    elif period == Period.QUARTER.value:
        start = end - timedelta(days=90)
    else:
        start = end - timedelta(days=7)
    return start, end


def _generate_category_distribution(total: int, rng: random.Random) -> dict[str, int]:
    """Generate a realistic distribution of reports across categories."""
    categories = [c.value for c in ReportCategory]
    weights = [0.25, 0.20, 0.15, 0.15, 0.10, 0.08, 0.07]
    distribution: dict[str, int] = {}
    remaining = total
    for i, cat in enumerate(categories[:-1]):
        count = int(total * weights[i] * rng.uniform(0.8, 1.2))
        count = min(count, remaining)
        distribution[cat] = count
        remaining -= count
    distribution[categories[-1]] = remaining
    return distribution


def _generate_action_distribution(resolved: int, rng: random.Random) -> dict[str, int]:
    """Generate a realistic distribution of moderation actions."""
    actions = [a.value for a in ModerationAction]
    weights = [0.30, 0.20, 0.15, 0.05, 0.20, 0.10]
    distribution: dict[str, int] = {}
    remaining = resolved
    for i, action in enumerate(actions[:-1]):
        count = int(resolved * weights[i] * rng.uniform(0.85, 1.15))
        count = min(count, remaining)
        distribution[action] = count
        remaining -= count
    distribution[actions[-1]] = remaining
    return distribution


def get_moderation_metrics(period: str = "week") -> ModerationMetrics:
    """Return moderation metrics for the specified period.

    Args:
        period: One of 'day', 'week', 'month', 'quarter'.

    Returns:
        ModerationMetrics with realistic mock data for the period.
    """
    rng = random.Random(hash(period) & 0xFFFFFFFF)
    start, end = _get_period_dates(period)

    # Scale base volume by period
    volume_multipliers = {"day": 15, "week": 80, "month": 320, "quarter": 900}
    multiplier = volume_multipliers.get(period, 80)
    total_reports = int(multiplier * rng.uniform(0.85, 1.15))

    resolution_rates = {"day": 0.92, "week": 0.88, "month": 0.85, "quarter": 0.82}
    resolved = int(total_reports * resolution_rates.get(period, 0.88))
    pending = total_reports - resolved

    avg_resolution = round(rng.uniform(2.0, 48.0), 1)
    category_dist = _generate_category_distribution(total_reports, rng)
    action_dist = _generate_action_distribution(resolved, rng)

    moderator_count = max(3, int(multiplier / 15))
    escalation_rate = round(rng.uniform(0.02, 0.12), 3)
    false_positive_rate = round(rng.uniform(0.03, 0.10), 3)
    satisfaction = round(rng.uniform(3.5, 4.7), 2)
    peak_hour = rng.randint(8, 22)
    repeat_rate = round(rng.uniform(0.05, 0.18), 3)

    return ModerationMetrics(
        period=period,
        start_date=start.isoformat(),
        end_date=end.isoformat(),
        total_reports=total_reports,
        resolved_reports=resolved,
        pending_reports=pending,
        avg_resolution_hours=avg_resolution,
        reports_by_category=category_dist,
        actions_taken=action_dist,
        moderator_count=moderator_count,
        escalation_rate=escalation_rate,
        false_positive_rate=false_positive_rate,
        community_satisfaction=satisfaction,
        peak_report_hour=peak_hour,
        repeat_offender_rate=repeat_rate,
    )


def analyze_moderation_trends(period: str = "week") -> TrendAnalysis:
    """Analyze moderation trends for the specified period.

    Compares current period metrics against a simulated previous period
    to identify changes, anomalies, and generate recommendations.

    Args:
        period: One of 'day', 'week', 'month', 'quarter'.

    Returns:
        TrendAnalysis with trend data, anomaly detection, and recommendations.
    """
    rng = random.Random(hash(period) & 0xFFFFFFFF)
    start, end = _get_period_dates(period)

    # Simulate previous-period comparison
    report_change = round(rng.uniform(-15.0, 25.0), 1)
    resolution_change = round(rng.uniform(-10.0, 15.0), 1)
    escalation_change = round(rng.uniform(-5.0, 8.0), 1)
    satisfaction_change = round(rng.uniform(-0.5, 0.5), 2)

    # Determine top growing/declining categories
    categories = [c.value for c in ReportCategory]
    cat_changes: dict[str, float] = {}
    for cat in categories:
        cat_changes[cat] = round(rng.uniform(-20.0, 30.0), 1)

    sorted_cats = sorted(cat_changes.items(), key=lambda x: x[1], reverse=True)
    top_growing = sorted_cats[0][0]
    top_declining = sorted_cats[-1][0]

    # Anomaly detection
    anomaly_detected = abs(report_change) > 20 or escalation_change > 5
    anomaly_desc: str | None = None
    if anomaly_detected:
        if report_change > 20:
            anomaly_desc = (
                f"Report volume surged {report_change}% above previous period. "
                "Possible coordinated attack or viral incident."
            )
        elif report_change < -20:
            anomaly_desc = (
                f"Report volume dropped {abs(report_change)}% below previous period. "
                "Verify reporting pipeline is functioning."
            )
        elif escalation_change > 5:
            anomaly_desc = (
                f"Escalation rate increased by {escalation_change} percentage points. "
                "Review moderator decision consistency."
            )

    # Generate recommendations
    recommendations: list[str] = []
    if report_change > 10:
        recommendations.append("Consider increasing moderator coverage during peak hours.")
    if resolution_change > 5:
        recommendations.append(
            "Resolution time is trending up. Review triage workflows and staffing."
        )
    if escalation_change > 3:
        recommendations.append(
            "Escalation rate rising. Provide additional moderator training on edge cases."
        )
    if satisfaction_change < -0.2:
        recommendations.append(
            "Community satisfaction declining. Survey users on moderation fairness."
        )
    if cat_changes.get(ReportCategory.SPAM.value, 0) > 15:
        recommendations.append(
            "Spam reports growing significantly. Evaluate automated spam filters."
        )
    if not recommendations:
        recommendations.append("Metrics are stable. Continue current moderation practices.")

    return TrendAnalysis(
        period=period,
        start_date=start.isoformat(),
        end_date=end.isoformat(),
        report_volume_change_pct=report_change,
        resolution_time_change_pct=resolution_change,
        escalation_rate_change_pct=escalation_change,
        satisfaction_change_pct=satisfaction_change,
        top_growing_category=top_growing,
        top_declining_category=top_declining,
        anomaly_detected=anomaly_detected,
        anomaly_description=anomaly_desc,
        recommendations=recommendations,
    )


def get_moderation_metrics_dict(period: str = "week") -> dict[str, Any]:
    """Return moderation metrics as a plain dictionary.

    Convenience wrapper around get_moderation_metrics for serialization.

    Args:
        period: One of 'day', 'week', 'month', 'quarter'.

    Returns:
        Dictionary representation of moderation metrics.
    """
    metrics = get_moderation_metrics(period)
    return {
        "period": metrics.period,
        "start_date": metrics.start_date,
        "end_date": metrics.end_date,
        "total_reports": metrics.total_reports,
        "resolved_reports": metrics.resolved_reports,
        "pending_reports": metrics.pending_reports,
        "avg_resolution_hours": metrics.avg_resolution_hours,
        "reports_by_category": metrics.reports_by_category,
        "actions_taken": metrics.actions_taken,
        "moderator_count": metrics.moderator_count,
        "escalation_rate": metrics.escalation_rate,
        "false_positive_rate": metrics.false_positive_rate,
        "community_satisfaction": metrics.community_satisfaction,
        "peak_report_hour": metrics.peak_report_hour,
        "repeat_offender_rate": metrics.repeat_offender_rate,
    }


def analyze_moderation_trends_dict(period: str = "week") -> dict[str, Any]:
    """Return trend analysis as a plain dictionary.

    Convenience wrapper around analyze_moderation_trends for serialization.

    Args:
        period: One of 'day', 'week', 'month', 'quarter'.

    Returns:
        Dictionary representation of trend analysis.
    """
    analysis = analyze_moderation_trends(period)
    return {
        "period": analysis.period,
        "start_date": analysis.start_date,
        "end_date": analysis.end_date,
        "report_volume_change_pct": analysis.report_volume_change_pct,
        "resolution_time_change_pct": analysis.resolution_time_change_pct,
        "escalation_rate_change_pct": analysis.escalation_rate_change_pct,
        "satisfaction_change_pct": analysis.satisfaction_change_pct,
        "top_growing_category": analysis.top_growing_category,
        "top_declining_category": analysis.top_declining_category,
        "anomaly_detected": analysis.anomaly_detected,
        "anomaly_description": analysis.anomaly_description,
        "recommendations": analysis.recommendations,
    }


# ---------------------------------------------------------------------------
# Community-scoped API (community_id-based)
# ---------------------------------------------------------------------------

_VALID_TIME_RANGES = {"7d", "30d", "90d", "1y"}


def _validate_community_id(community_id: str) -> None:
    """Validate that community_id is a non-empty string."""
    if not isinstance(community_id, str) or not community_id.strip():
        raise ValueError("community_id must be a non-empty string")


def _validate_time_range(time_range: str) -> None:
    """Validate that time_range is one of the allowed values."""
    if time_range not in _VALID_TIME_RANGES:
        raise ValueError(
            f"time_range must be one of {sorted(_VALID_TIME_RANGES)}, got '{time_range}'"
        )


def _fetch_metrics_from_store(community_id: str) -> dict[str, Any]:
    """Fetch raw moderation metrics from the data store.

    Placeholder: replace with actual database or analytics backend query.
    Returns an empty dict if no data is available.
    """
    return {}


def _fetch_trends_from_store(community_id: str, time_range: str) -> dict[str, Any]:
    """Fetch raw moderation trends from the data store.

    Placeholder: replace with actual database or analytics backend query.
    Returns an empty dict if no data is available.
    """
    return {}


def get_moderation_metrics(community_id: str) -> dict[str, Any]:
    """Get moderation metrics for a community.

    Args:
        community_id: The unique identifier of the community.

    Returns:
        A dictionary containing moderation metrics such as total_actions,
        actions_by_type, active_moderators, and resolution_rate.

    Raises:
        ValueError: If community_id is empty or not a string.
        RuntimeError: If metrics cannot be retrieved.
    """
    _validate_community_id(community_id)

    try:
        raw = _fetch_metrics_from_store(community_id)
    except Exception as exc:
        raise RuntimeError(
            f"Failed to retrieve moderation metrics for community '{community_id}'"
        ) from exc

    metrics: dict[str, Any] = {
        "community_id": community_id,
        "total_actions": raw.get("total_actions", 0),
        "actions_by_type": raw.get("actions_by_type", {}),
        "active_moderators": raw.get("active_moderators", 0),
        "resolution_rate": raw.get("resolution_rate", 0.0),
        "pending_reports": raw.get("pending_reports", 0),
        "timestamp": datetime.now().isoformat(),
    }

    return metrics


def get_moderation_trends(community_id: str, time_range: str) -> dict[str, Any]:
    """Get moderation trends for a community over a time range.

    Args:
        community_id: The unique identifier of the community.
        time_range: The time window for trends. One of '7d', '30d', '90d', '1y'.

    Returns:
        A dictionary containing trend data including daily_counts,
        peak_activity_day, and change_percentage.

    Raises:
        ValueError: If community_id is empty or time_range is invalid.
        RuntimeError: If trends cannot be retrieved.
    """
    _validate_community_id(community_id)
    _validate_time_range(time_range)

    try:
        raw = _fetch_trends_from_store(community_id, time_range)
    except Exception as exc:
        raise RuntimeError(
            f"Failed to retrieve moderation trends for community '{community_id}'"
        ) from exc

    trends: dict[str, Any] = {
        "community_id": community_id,
        "time_range": time_range,
        "daily_counts": raw.get("daily_counts", []),
        "peak_activity_day": raw.get("peak_activity_day"),
        "change_percentage": raw.get("change_percentage", 0.0),
        "timestamp": datetime.now().isoformat(),
    }

    return trends


def flag_moderation_anomaly(community_id: str) -> bool:
    """Flag whether a community has a moderation anomaly.

    An anomaly is detected when there is a significant spike in moderation
    actions relative to historical averages, or when resolution rates drop
    below acceptable thresholds.

    Args:
        community_id: The unique identifier of the community.

    Returns:
        True if an anomaly is detected, False otherwise.

    Raises:
        ValueError: If community_id is empty or not a string.
        RuntimeError: If anomaly detection fails.
    """
    _validate_community_id(community_id)

    try:
        metrics = get_moderation_metrics(community_id)
        trends = get_moderation_trends(community_id, "7d")
    except Exception as exc:
        raise RuntimeError(
            f"Failed to detect moderation anomaly for community '{community_id}'"
        ) from exc

    # Anomaly heuristics
    resolution_rate = metrics.get("resolution_rate", 1.0)
    change_percentage = trends.get("change_percentage", 0.0)
    pending_reports = metrics.get("pending_reports", 0)

    is_anomaly = resolution_rate < 0.5 or change_percentage > 200.0 or pending_reports > 100

    return is_anomaly
