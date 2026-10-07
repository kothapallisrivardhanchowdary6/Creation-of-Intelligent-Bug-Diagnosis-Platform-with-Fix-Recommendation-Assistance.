"""
Milestone 4.1 — Defect Pattern Analytics Router.

Endpoints:
  GET /api/analytics/overview     — Total bugs, severity/priority counts, top components
  GET /api/analytics/severity     — Severity distribution
  GET /api/analytics/priority     — Priority distribution
  GET /api/analytics/components   — Component-wise bug frequency
  GET /api/analytics/exceptions   — Exception-type frequency
  GET /api/analytics/root-causes  — Most common root causes
  GET /api/analytics/duplicates   — Duplicate vs unique bugs
  GET /api/analytics/trends       — Defect trends over time
  GET /api/analytics/clusters     — Semantically similar bug clusters (via ChromaDB)

All analytics are computed against REAL data: submitted bugs in bug_store,
their analysis results, and the ChromaDB historical-defect knowledge base.
Filtering is applied via query parameters — no hardcoded values anywhere.
"""

import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query

# Import the live bug store from bugs router (same process, same dict)
from routers.bugs import bug_store, get_chroma_service, get_embedding_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["analytics"])


# ── Helpers ────────────────────────────────────────────────────────────────────

def _all_bugs() -> List[Dict[str, Any]]:
    """Return all bugs from the in-memory store."""
    return list(bug_store.values())


def _analyzed_bugs() -> List[Dict[str, Any]]:
    """Return only bugs that have completed analysis."""
    return [b for b in _all_bugs() if b.get("analysis")]


def _apply_filters(
    bugs: List[Dict],
    component: Optional[str] = None,
    severity: Optional[str] = None,
    priority: Optional[str] = None,
    exception_type: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    is_duplicate: Optional[bool] = None,
) -> List[Dict]:
    """Apply query-parameter filters to a bug list."""
    filtered = bugs

    if component:
        comp_lower = component.lower()
        filtered = [
            b for b in filtered
            if _get_component(b).lower() == comp_lower
        ]

    if severity:
        sev_lower = severity.lower()
        filtered = [
            b for b in filtered
            if _get_severity(b).lower() == sev_lower
        ]

    if priority:
        prio_upper = priority.upper()
        filtered = [
            b for b in filtered
            if _get_priority(b).upper() == prio_upper
        ]

    if exception_type:
        exc_lower = exception_type.lower()
        filtered = [
            b for b in filtered
            if any(
                exc_lower in (e.get("exception_type") or e.get("type") or "").lower()
                for e in _get_exceptions(b)
            )
        ]

    if date_from:
        try:
            dt_from = datetime.fromisoformat(date_from.replace("Z", "+00:00"))
            filtered = [
                b for b in filtered
                if datetime.fromisoformat(
                    b.get("created_at", "2000-01-01").replace("Z", "+00:00")
                ) >= dt_from
            ]
        except ValueError:
            pass

    if date_to:
        try:
            dt_to = datetime.fromisoformat(date_to.replace("Z", "+00:00"))
            filtered = [
                b for b in filtered
                if datetime.fromisoformat(
                    b.get("created_at", "2099-01-01").replace("Z", "+00:00")
                ) <= dt_to
            ]
        except ValueError:
            pass

    if is_duplicate is not None:
        filtered = [
            b for b in filtered
            if _is_duplicate(b) == is_duplicate
        ]

    return filtered


# ── Field extractors ──────────────────────────────────────────────────────────

def _get_triage(bug: Dict) -> Dict:
    analysis = bug.get("analysis") or {}
    return analysis.get("triage") or {}


def _get_severity(bug: Dict) -> str:
    return _get_triage(bug).get("severity") or "unknown"


def _get_priority(bug: Dict) -> str:
    return _get_triage(bug).get("priority") or "unknown"


def _get_component(bug: Dict) -> str:
    return _get_triage(bug).get("component") or "Unknown"


def _get_category(bug: Dict) -> str:
    return _get_triage(bug).get("category") or "Unknown"


def _get_exceptions(bug: Dict) -> List[Dict]:
    analysis = bug.get("analysis") or {}
    log_analysis = analysis.get("log_analysis") or {}
    return log_analysis.get("exceptions") or []


def _get_root_cause(bug: Dict) -> str:
    analysis = bug.get("analysis") or {}
    rc = analysis.get("root_cause") or {}
    return rc.get("probable_cause") or ""


def _get_root_cause_status(bug: Dict) -> str:
    analysis = bug.get("analysis") or {}
    rc = analysis.get("root_cause") or {}
    return rc.get("status") or "unknown"


def _is_duplicate(bug: Dict) -> bool:
    analysis = bug.get("analysis") or {}
    dd = analysis.get("duplicate_detection") or {}
    classification = dd.get("classification") or ""
    return classification == "likely_duplicate"


def _get_remediation(bug: Dict) -> str:
    analysis = bug.get("analysis") or {}
    rem = analysis.get("remediation") or {}
    return rem.get("suggested_fix") or ""


def _get_resolution_status(bug: Dict) -> str:
    """Derive resolution status from available data."""
    analysis = bug.get("analysis")
    if not analysis:
        return "unanalyzed"
    rem = analysis.get("remediation") or {}
    if rem.get("status") == "success" and rem.get("suggested_fix"):
        return "has_remediation"
    return "analyzed_no_fix"


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/overview")
async def analytics_overview(
    component: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    exception_type: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    is_duplicate: Optional[bool] = Query(None),
):
    """
    Top-level analytics overview.

    Returns totals, severity/priority distribution, top components,
    top exceptions, and duplicate statistics — all from real submitted bugs.
    """
    all_bugs = _all_bugs()
    filtered = _apply_filters(
        all_bugs, component, severity, priority, exception_type,
        date_from, date_to, is_duplicate
    )
    analyzed = [b for b in filtered if b.get("analysis")]

    # Severity distribution
    severity_dist: Dict[str, int] = defaultdict(int)
    for b in analyzed:
        sev = _get_severity(b)
        severity_dist[sev] += 1

    # Priority distribution
    priority_dist: Dict[str, int] = defaultdict(int)
    for b in analyzed:
        prio = _get_priority(b)
        priority_dist[prio] += 1

    # Top components
    component_counts: Dict[str, int] = defaultdict(int)
    for b in analyzed:
        component_counts[_get_component(b)] += 1
    top_components = [
        {"component": k, "count": v}
        for k, v in sorted(component_counts.items(), key=lambda x: -x[1])
    ][:10]

    # Top exceptions
    exception_counts: Dict[str, int] = defaultdict(int)
    for b in analyzed:
        for exc in _get_exceptions(b):
            exc_type = exc.get("exception_type") or exc.get("type") or "Unknown"
            if exc_type and exc_type != "Unknown":
                exception_counts[exc_type] += 1
    top_exceptions = [
        {"exception": k, "count": v}
        for k, v in sorted(exception_counts.items(), key=lambda x: -x[1])
    ][:10]

    # Duplicate stats
    duplicates = sum(1 for b in analyzed if _is_duplicate(b))
    unique = len(analyzed) - duplicates

    # Resolution stats
    resolution_dist: Dict[str, int] = defaultdict(int)
    for b in filtered:
        resolution_dist[_get_resolution_status(b)] += 1

    # ChromaDB KB stats
    try:
        chroma = get_chroma_service()
        kb_status = chroma.get_status()
    except Exception:
        kb_status = {"total_documents": 0, "status": "unavailable"}

    return {
        "total_bugs": len(filtered),
        "analyzed_bugs": len(analyzed),
        "unanalyzed_bugs": len(filtered) - len(analyzed),
        "severity_distribution": dict(severity_dist),
        "priority_distribution": dict(priority_dist),
        "top_components": top_components,
        "top_exceptions": top_exceptions,
        "duplicate_stats": {
            "duplicates": duplicates,
            "unique": unique,
            "duplicate_rate": round(duplicates / max(len(analyzed), 1), 3),
        },
        "resolution_distribution": dict(resolution_dist),
        "knowledge_base": kb_status,
        "filters_applied": {
            "component": component,
            "severity": severity,
            "priority": priority,
            "exception_type": exception_type,
            "date_from": date_from,
            "date_to": date_to,
            "is_duplicate": is_duplicate,
        },
    }


@router.get("/severity")
async def analytics_severity(
    component: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
):
    """Severity distribution with component breakdown."""
    analyzed = [b for b in _all_bugs() if b.get("analysis")]
    filtered = _apply_filters(analyzed, component=component, priority=priority,
                               date_from=date_from, date_to=date_to)

    severity_dist: Dict[str, int] = defaultdict(int)
    severity_by_component: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))

    for b in filtered:
        sev = _get_severity(b)
        comp = _get_component(b)
        severity_dist[sev] += 1
        severity_by_component[comp][sev] += 1

    # Severity over time (by week)
    weekly: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for b in filtered:
        created = b.get("created_at", "")
        try:
            dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
            week_key = dt.strftime("%Y-W%V")
        except Exception:
            week_key = "unknown"
        sev = _get_severity(b)
        weekly[week_key][sev] += 1

    return {
        "severity_distribution": dict(severity_dist),
        "severity_by_component": {k: dict(v) for k, v in severity_by_component.items()},
        "severity_over_time": {k: dict(v) for k, v in sorted(weekly.items())},
        "total": len(filtered),
    }


@router.get("/priority")
async def analytics_priority(
    component: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
):
    """Priority distribution with severity correlation."""
    analyzed = [b for b in _all_bugs() if b.get("analysis")]
    filtered = _apply_filters(analyzed, component=component, severity=severity,
                               date_from=date_from, date_to=date_to)

    priority_dist: Dict[str, int] = defaultdict(int)
    priority_by_severity: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))

    for b in filtered:
        prio = _get_priority(b)
        sev = _get_severity(b)
        priority_dist[prio] += 1
        priority_by_severity[sev][prio] += 1

    return {
        "priority_distribution": dict(priority_dist),
        "priority_by_severity": {k: dict(v) for k, v in priority_by_severity.items()},
        "total": len(filtered),
    }


@router.get("/components")
async def analytics_components(
    severity: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
):
    """Component-wise bug frequency with severity breakdown."""
    analyzed = [b for b in _all_bugs() if b.get("analysis")]
    filtered = _apply_filters(analyzed, severity=severity, priority=priority,
                               date_from=date_from, date_to=date_to)

    component_data: Dict[str, Dict] = defaultdict(lambda: {
        "total": 0, "critical": 0, "high": 0, "medium": 0, "low": 0, "unknown": 0
    })

    for b in filtered:
        comp = _get_component(b)
        sev = _get_severity(b)
        component_data[comp]["total"] += 1
        component_data[comp][sev] = component_data[comp].get(sev, 0) + 1

    sorted_components = sorted(
        [{"component": k, **v} for k, v in component_data.items()],
        key=lambda x: -x["total"]
    )

    return {
        "components": sorted_components,
        "total_components": len(sorted_components),
        "most_affected": sorted_components[0]["component"] if sorted_components else None,
        "total": len(filtered),
    }


@router.get("/exceptions")
async def analytics_exceptions(
    component: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
):
    """Exception-type frequency analysis."""
    analyzed = [b for b in _all_bugs() if b.get("analysis")]
    filtered = _apply_filters(analyzed, component=component, severity=severity,
                               date_from=date_from, date_to=date_to)

    exception_counts: Dict[str, int] = defaultdict(int)
    exception_by_component: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    error_patterns: Dict[str, int] = defaultdict(int)

    for b in filtered:
        comp = _get_component(b)
        for exc in _get_exceptions(b):
            exc_type = exc.get("exception_type") or exc.get("type") or "Unknown"
            exception_counts[exc_type] += 1
            exception_by_component[comp][exc_type] += 1

        # Collect error patterns
        analysis = b.get("analysis") or {}
        log_a = analysis.get("log_analysis") or {}
        for pat in log_a.get("error_patterns") or []:
            if pat:
                error_patterns[pat] += 1

    sorted_exceptions = [
        {"exception": k, "count": v}
        for k, v in sorted(exception_counts.items(), key=lambda x: -x[1])
    ]
    sorted_patterns = [
        {"pattern": k, "count": v}
        for k, v in sorted(error_patterns.items(), key=lambda x: -x[1])
    ][:15]

    return {
        "exception_distribution": sorted_exceptions,
        "exception_by_component": {k: dict(v) for k, v in exception_by_component.items()},
        "error_patterns": sorted_patterns,
        "unique_exception_types": len(exception_counts),
        "total": len(filtered),
    }


@router.get("/root-causes")
async def analytics_root_causes(
    component: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
):
    """Most common root causes with confidence distribution."""
    analyzed = [b for b in _all_bugs() if b.get("analysis")]
    filtered = _apply_filters(analyzed, component=component, severity=severity,
                               date_from=date_from, date_to=date_to)

    root_cause_counts: Dict[str, int] = defaultdict(int)
    root_cause_by_component: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    rc_status_counts: Dict[str, int] = defaultdict(int)
    confidence_buckets = {"high_90+": 0, "medium_70_90": 0, "low_50_70": 0, "very_low_50-": 0}

    for b in filtered:
        analysis = b.get("analysis") or {}
        rc = analysis.get("root_cause") or {}
        status = rc.get("status") or "unknown"
        rc_status_counts[status] += 1

        cause = rc.get("probable_cause") or ""
        comp = _get_component(b)

        if cause and status == "success":
            # Truncate very long causes for grouping
            cause_key = cause[:80] if len(cause) > 80 else cause
            root_cause_counts[cause_key] += 1
            root_cause_by_component[comp][cause_key] += 1

        # Confidence bucketing
        confidence = rc.get("confidence") or 0
        if confidence >= 0.90:
            confidence_buckets["high_90+"] += 1
        elif confidence >= 0.70:
            confidence_buckets["medium_70_90"] += 1
        elif confidence >= 0.50:
            confidence_buckets["low_50_70"] += 1
        else:
            confidence_buckets["very_low_50-"] += 1

    top_root_causes = [
        {"cause": k, "count": v}
        for k, v in sorted(root_cause_counts.items(), key=lambda x: -x[1])
    ][:10]

    return {
        "top_root_causes": top_root_causes,
        "root_cause_status": dict(rc_status_counts),
        "confidence_distribution": confidence_buckets,
        "total": len(filtered),
    }


@router.get("/duplicates")
async def analytics_duplicates(
    component: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
):
    """Duplicate detection statistics."""
    analyzed = [b for b in _all_bugs() if b.get("analysis")]
    filtered = _apply_filters(analyzed, component=component, severity=severity,
                               date_from=date_from, date_to=date_to)

    classification_counts: Dict[str, int] = defaultdict(int)
    similarity_buckets = {"very_high_90+": 0, "high_80_90": 0, "medium_55_80": 0, "low_55-": 0}
    duplicate_by_component: Dict[str, int] = defaultdict(int)

    total = len(filtered)
    duplicates = 0

    for b in filtered:
        analysis = b.get("analysis") or {}
        dd = analysis.get("duplicate_detection") or {}
        classification = dd.get("classification") or "unknown"
        classification_counts[classification] += 1

        if classification == "likely_duplicate":
            duplicates += 1
            duplicate_by_component[_get_component(b)] += 1

        top_sim = dd.get("top_match_similarity") or 0
        if top_sim >= 0.90:
            similarity_buckets["very_high_90+"] += 1
        elif top_sim >= 0.80:
            similarity_buckets["high_80_90"] += 1
        elif top_sim >= 0.55:
            similarity_buckets["medium_55_80"] += 1
        else:
            similarity_buckets["low_55-"] += 1

    unique = total - duplicates

    return {
        "total_analyzed": total,
        "duplicates": duplicates,
        "unique": unique,
        "related_issues": classification_counts.get("related_issue", 0),
        "duplicate_rate": round(duplicates / max(total, 1), 3),
        "classification_distribution": dict(classification_counts),
        "similarity_distribution": similarity_buckets,
        "duplicates_by_component": dict(
            sorted(duplicate_by_component.items(), key=lambda x: -x[1])
        ),
    }


@router.get("/trends")
async def analytics_trends(
    component: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    granularity: str = Query("day", description="day | week | month"),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
):
    """Defect trends over time."""
    all_bugs = _all_bugs()
    filtered = _apply_filters(all_bugs, component=component, severity=severity,
                               date_from=date_from, date_to=date_to)

    # Group by time bucket
    time_buckets: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))

    fmt_map = {"day": "%Y-%m-%d", "week": "%Y-W%V", "month": "%Y-%m"}
    fmt = fmt_map.get(granularity, "%Y-%m-%d")

    for b in filtered:
        created = b.get("created_at", "")
        try:
            dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
            bucket = dt.strftime(fmt)
        except Exception:
            bucket = "unknown"

        sev = _get_severity(b) if b.get("analysis") else "unanalyzed"
        time_buckets[bucket]["total"] += 1
        time_buckets[bucket][sev] += 1

    # Also include historical defect data from ChromaDB metadata
    # (to give richer trend data even when few bugs submitted)
    chroma_trend: Dict[str, int] = {}
    try:
        chroma = get_chroma_service()
        docs = chroma.get_all_documents()
        for doc in docs:
            meta = doc.get("metadata") or {}
            created = meta.get("created_at") or meta.get("timestamp") or ""
            try:
                dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                bucket = dt.strftime(fmt)
                chroma_trend[bucket] = chroma_trend.get(bucket, 0) + 1
            except Exception:
                pass
    except Exception:
        pass

    # Build sorted trend series
    all_buckets = sorted(set(list(time_buckets.keys()) + list(chroma_trend.keys())))
    trend_series = []
    for bucket in all_buckets:
        if bucket == "unknown":
            continue
        entry = {
            "period": bucket,
            **{k: v for k, v in time_buckets.get(bucket, {}).items()},
            "total": time_buckets.get(bucket, {}).get("total", 0),
            "historical_kb_entries": chroma_trend.get(bucket, 0),
        }
        trend_series.append(entry)

    # If no real submitted bugs yet, synthesize trend from last 14 days
    if not [b for b in filtered if b.get("created_at")]:
        now = datetime.utcnow()
        trend_series = [
            {
                "period": (now - timedelta(days=i)).strftime(fmt),
                "total": 0,
                "historical_kb_entries": 0,
            }
            for i in range(13, -1, -1)
        ]

    return {
        "granularity": granularity,
        "trend_series": trend_series,
        "total_bugs": len(filtered),
        "date_range": {
            "from": min((b.get("created_at", "") for b in filtered), default=None),
            "to": max((b.get("created_at", "") for b in filtered), default=None),
        },
    }


@router.get("/clusters")
async def analytics_clusters(
    top_k: int = Query(5, ge=1, le=20),
    min_similarity: float = Query(0.55, ge=0.0, le=1.0),
):
    """
    Semantically similar bug clusters from the ChromaDB knowledge base.

    Uses existing embedding infrastructure — no second vector store.
    """
    try:
        chroma = get_chroma_service()
        embedding_service = get_embedding_service()

        # Pull a sample of KB documents for cluster analysis
        all_docs = chroma.get_all_documents(limit=200)

        if not all_docs:
            return {
                "clusters": [],
                "total_documents": 0,
                "message": "Knowledge base is empty. Seed data first.",
            }

        # Group by component (simple clustering using metadata)
        component_clusters: Dict[str, List[Dict]] = defaultdict(list)
        for doc in all_docs:
            meta = doc.get("metadata") or {}
            comp = meta.get("component") or "Unknown"
            component_clusters[comp].append({
                "id": doc.get("id", ""),
                "document": (doc.get("document") or "")[:120],
                "severity": meta.get("severity") or "unknown",
                "component": comp,
                "project": meta.get("project") or "unknown",
            })

        # Build cluster summaries
        clusters = []
        for comp, docs in sorted(
            component_clusters.items(), key=lambda x: -len(x[1])
        )[:top_k]:
            severities: Dict[str, int] = defaultdict(int)
            for d in docs:
                severities[d["severity"]] += 1
            clusters.append({
                "cluster_id": f"cluster_{comp.lower().replace(' ', '_')}",
                "label": comp,
                "size": len(docs),
                "representative_bugs": docs[:5],
                "severity_breakdown": dict(severities),
            })

        # Submitted bugs — find similar groups using embedding search
        submitted_bugs = _analyzed_bugs()
        submitted_clusters = []
        if submitted_bugs and embedding_service:
            for bug in submitted_bugs[:top_k]:
                query = f"{bug.get('title', '')} {bug.get('description', '')[:200]}"
                try:
                    emb = embedding_service.embed_text(query)
                    similar = chroma.search(emb, top_k=3)
                    high_sim = [s for s in similar if s.get("score", 0) >= min_similarity]
                    if high_sim:
                        submitted_clusters.append({
                            "submitted_bug_id": bug["id"],
                            "submitted_bug_title": bug.get("title", ""),
                            "similar_kb_bugs": [
                                {
                                    "id": s["id"],
                                    "document": (s.get("document") or "")[:100],
                                    "similarity": round(s.get("score", 0), 3),
                                    "component": (s.get("metadata") or {}).get("component"),
                                }
                                for s in high_sim
                            ],
                        })
                except Exception as e:
                    logger.warning(f"Cluster search failed for bug {bug['id']}: {e}")

        return {
            "kb_clusters": clusters,
            "submitted_bug_clusters": submitted_clusters,
            "total_documents": len(all_docs),
            "min_similarity_threshold": min_similarity,
        }

    except Exception as e:
        logger.error(f"Cluster analytics failed: {e}", exc_info=True)
        return {
            "clusters": [],
            "total_documents": 0,
            "error": str(e),
        }


@router.get("/remediation-patterns")
async def analytics_remediation_patterns(
    component: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
):
    """Common remediation patterns across analyzed bugs."""
    analyzed = [b for b in _all_bugs() if b.get("analysis")]
    filtered = _apply_filters(analyzed, component=component, severity=severity)

    fix_source_dist: Dict[str, int] = defaultdict(int)
    effort_dist: Dict[str, int] = defaultdict(int)
    risk_dist: Dict[str, int] = defaultdict(int)
    common_steps: Dict[str, int] = defaultdict(int)

    for b in filtered:
        analysis = b.get("analysis") or {}
        rem = analysis.get("remediation") or {}
        if not rem:
            continue

        fix_source_dist[rem.get("fix_source") or "unknown"] += 1
        effort_dist[rem.get("estimated_effort") or "unknown"] += 1
        risk_dist[rem.get("risk_level") or "unknown"] += 1

        for step in rem.get("implementation_steps") or []:
            s = step.get("step") if isinstance(step, dict) else str(step)
            if s:
                # Normalize step text
                key = s[:60]
                common_steps[key] += 1

    return {
        "fix_source_distribution": dict(fix_source_dist),
        "effort_distribution": dict(effort_dist),
        "risk_distribution": dict(risk_dist),
        "common_steps": [
            {"step": k, "count": v}
            for k, v in sorted(common_steps.items(), key=lambda x: -x[1])
        ][:10],
        "total": len(filtered),
    }
