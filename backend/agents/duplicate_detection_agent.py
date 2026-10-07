"""
Milestone 3: Duplicate Detection Agent.

Uses the existing EmbeddingService and ChromaService to search both historical
and submitted bugs.  Returns real cosine-similarity scores (no mock values),
classifies each match, and applies configurable thresholds.

Classification:
  likely_duplicate     — similarity >= LIKELY_DUPLICATE_THRESHOLD
  related_issue        — similarity >= RELATED_ISSUE_THRESHOLD
  new_unmatched        — all matches below thresholds
  insufficient_evidence — no embedding / no knowledge base available
"""

import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)


# ============================================================
# Configurable thresholds
# ============================================================
LIKELY_DUPLICATE_THRESHOLD: float = 0.82   # >= this → likely_duplicate
RELATED_ISSUE_THRESHOLD: float = 0.55      # >= this → related_issue
# below RELATED_ISSUE_THRESHOLD → new_unmatched


# ============================================================
# Pydantic Models
# ============================================================

class MatchedBug(BaseModel):
    """A single matching bug from the knowledge base."""
    bug_id: str
    title: str                       # document text
    similarity_score: float = Field(ge=0.0, le=1.0)
    classification: str              # likely_duplicate | related_issue | new_unmatched
    component: Optional[str] = None
    severity: Optional[str] = None
    exception_type: Optional[str] = None
    resolution_summary: Optional[str] = None

    @validator("similarity_score")
    def round_score(cls, v):
        return round(v, 4)


class DuplicateDetectionResult(BaseModel):
    """Complete duplicate detection result."""
    classification: str              # overall: likely_duplicate | related_issue | new_unmatched | insufficient_evidence
    top_match_similarity: float = Field(ge=0.0, le=1.0, default=0.0)
    duplicate_probability: float = Field(ge=0.0, le=1.0, default=0.0)
    matched_bugs: List[MatchedBug] = Field(default_factory=list)
    analysis_summary: str = ""
    thresholds_used: Dict[str, float] = Field(default_factory=dict)

    # Keep legacy fields for backward-compat with frontend
    is_duplicate: bool = False
    similarity_score: float = Field(ge=0.0, le=1.0, default=0.0)
    matching_bugs: List[Dict[str, Any]] = Field(default_factory=list)


class DuplicateDetectionAgentOutput(BaseModel):
    """Complete agent output with metadata."""
    agent: str = "Duplicate Detection Agent"
    version: str = "3.0.0-M3"
    result: DuplicateDetectionResult
    duration: float
    timestamp: str
    status: str = "success"
    error: Optional[str] = None


# ============================================================
# Duplicate Detection Agent
# ============================================================

class DuplicateDetectionAgent:
    """
    Milestone 3 Duplicate Detection Agent.

    1. Embeds the current bug using the real EmbeddingService.
    2. Searches ChromaDB for top-k similar defects.
    3. Assigns per-match classification using configurable thresholds.
    4. Returns a structured result with REAL similarity scores.
    """

    def __init__(
        self,
        chroma_service=None,
        embedding_service=None,
        likely_duplicate_threshold: float = LIKELY_DUPLICATE_THRESHOLD,
        related_issue_threshold: float = RELATED_ISSUE_THRESHOLD,
        top_k: int = 5,
    ):
        self.chroma = chroma_service
        self.embeddings = embedding_service
        self.likely_duplicate_threshold = likely_duplicate_threshold
        self.related_issue_threshold = related_issue_threshold
        self.top_k = top_k
        self.name = "Duplicate Detection Agent"
        self.version = "3.0.0-M3"

    async def analyze(self, bug_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detect potential duplicate bugs.

        Args:
            bug_data: The current bug report dict.

        Returns:
            DuplicateDetectionAgentOutput as dict.
        """
        start_time = time.time()

        try:
            if not self.embeddings or not self.chroma:
                return self._insufficient_evidence(
                    "Embedding service or vector store unavailable.",
                    time.time() - start_time,
                )

            # ── 1. Build query text ───────────────────────────────────────
            query_text = self._build_query(bug_data)
            if not query_text.strip():
                return self._insufficient_evidence(
                    "Insufficient bug data to build a meaningful query.",
                    time.time() - start_time,
                )

            # ── 2. Embed and search ────────────────────────────────────────
            try:
                query_embedding = self.embeddings.embed_text(query_text)
                raw_results = self.chroma.search(query_embedding, top_k=self.top_k)
            except Exception as e:
                logger.error(f"Embedding/search failed: {e}")
                return self._insufficient_evidence(
                    f"Search failed: {str(e)}", time.time() - start_time
                )

            if not raw_results:
                return self._no_matches(time.time() - start_time)

            # ── 3. Classify each match ─────────────────────────────────────
            matched_bugs = []
            for r in raw_results:
                score = float(r.get("score", 0.0))
                meta = r.get("metadata", {})
                classification = self._classify_match(score)
                matched_bugs.append(
                    MatchedBug(
                        bug_id=r.get("id", "UNKNOWN"),
                        title=r.get("document", ""),
                        similarity_score=score,
                        classification=classification,
                        component=meta.get("component", meta.get("project", "")),
                        severity=meta.get("severity", ""),
                        exception_type=meta.get("exception_type", ""),
                        resolution_summary=meta.get("resolution", ""),
                    )
                )

            # ── 4. Compute overall result ──────────────────────────────────
            top_score = matched_bugs[0].similarity_score if matched_bugs else 0.0
            overall_classification = self._overall_classification(matched_bugs)
            duplicate_probability = self._compute_duplicate_probability(matched_bugs)

            analysis_summary = self._build_summary(
                matched_bugs, top_score, overall_classification
            )

            # Legacy-compat fields (used by older frontend paths)
            legacy_matching_bugs = [
                {
                    "bugId": mb.bug_id,
                    "title": mb.title,
                    "similarity": mb.similarity_score,
                    "project": mb.component or "Unknown",
                    "component": mb.component or "Unknown",
                    "severity": mb.severity or "unknown",
                    "resolution": mb.resolution_summary or "N/A",
                }
                for mb in matched_bugs
            ]

            result = DuplicateDetectionResult(
                classification=overall_classification,
                top_match_similarity=top_score,
                duplicate_probability=duplicate_probability,
                matched_bugs=matched_bugs,
                analysis_summary=analysis_summary,
                thresholds_used={
                    "likely_duplicate": self.likely_duplicate_threshold,
                    "related_issue": self.related_issue_threshold,
                },
                # legacy
                is_duplicate=(overall_classification == "likely_duplicate"),
                similarity_score=top_score,
                matching_bugs=legacy_matching_bugs,
            )

            duration = time.time() - start_time
            logger.info(
                f"Duplicate Detection Agent completed in {duration:.2f}s — "
                f"classification={overall_classification}, top_score={top_score:.3f}"
            )

            output = DuplicateDetectionAgentOutput(
                result=result,
                duration=duration,
                timestamp=datetime.utcnow().isoformat(),
                status="success",
            )
            return output.dict()

        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Duplicate Detection Agent failed: {e}", exc_info=True)
            return DuplicateDetectionAgentOutput(
                result=DuplicateDetectionResult(
                    classification="insufficient_evidence",
                    analysis_summary=f"Agent error: {str(e)}",
                ),
                duration=duration,
                timestamp=datetime.utcnow().isoformat(),
                status="error",
                error=str(e),
            ).dict()

    # ──────────────────────────────────────────────────────────────────────
    # Private helpers
    # ──────────────────────────────────────────────────────────────────────

    def _build_query(self, bug_data: Dict[str, Any]) -> str:
        """Combine title, description, and key fields into a search query."""
        parts = [
            bug_data.get("title", ""),
            bug_data.get("description", ""),
            bug_data.get("stack_trace", "")[:300] if bug_data.get("stack_trace") else "",
        ]
        return " ".join(p for p in parts if p).strip()

    def _classify_match(self, score: float) -> str:
        """Classify a single similarity score."""
        if score >= self.likely_duplicate_threshold:
            return "likely_duplicate"
        elif score >= self.related_issue_threshold:
            return "related_issue"
        else:
            return "new_unmatched"

    def _overall_classification(self, matches: List[MatchedBug]) -> str:
        """Determine overall classification from the match list."""
        if not matches:
            return "new_unmatched"
        classifications = {m.classification for m in matches}
        if "likely_duplicate" in classifications:
            return "likely_duplicate"
        if "related_issue" in classifications:
            return "related_issue"
        return "new_unmatched"

    def _compute_duplicate_probability(self, matches: List[MatchedBug]) -> float:
        """
        Weighted probability score.
        Top match contributes 60%, second 25%, third 15%.
        """
        if not matches:
            return 0.0
        weights = [0.60, 0.25, 0.15]
        score = 0.0
        for i, m in enumerate(matches[:3]):
            # Only count matches above the related threshold
            if m.similarity_score >= self.related_issue_threshold:
                score += weights[i] * m.similarity_score
        return round(min(1.0, score), 4)

    def _build_summary(
        self,
        matches: List[MatchedBug],
        top_score: float,
        classification: str,
    ) -> str:
        """Human-readable summary of duplicate detection result."""
        n = len(matches)
        label = {
            "likely_duplicate": "⚠ Likely Duplicate",
            "related_issue": "Related Issue",
            "new_unmatched": "New / Unique Bug",
            "insufficient_evidence": "Insufficient Evidence",
        }.get(classification, classification)

        summary = (
            f"{label} — {n} candidate(s) found. "
            f"Highest similarity: {top_score:.1%}."
        )
        if classification == "likely_duplicate" and matches:
            summary += f" Closest match: {matches[0].bug_id} ({matches[0].similarity_score:.1%})."
        elif classification == "related_issue":
            related = [m for m in matches if m.classification == "related_issue"]
            summary += f" {len(related)} related issue(s) found."
        return summary

    def _no_matches(self, duration: float) -> Dict[str, Any]:
        """Return result when no matches found."""
        return DuplicateDetectionAgentOutput(
            result=DuplicateDetectionResult(
                classification="new_unmatched",
                top_match_similarity=0.0,
                duplicate_probability=0.0,
                analysis_summary="No similar historical defects found. This appears to be a new, unique bug.",
                thresholds_used={
                    "likely_duplicate": self.likely_duplicate_threshold,
                    "related_issue": self.related_issue_threshold,
                },
                is_duplicate=False,
                similarity_score=0.0,
            ),
            duration=duration,
            timestamp=datetime.utcnow().isoformat(),
            status="success",
        ).dict()

    def _insufficient_evidence(self, reason: str, duration: float) -> Dict[str, Any]:
        """Return insufficient evidence result."""
        logger.info(f"Duplicate Detection Agent: Insufficient Evidence — {reason}")
        return DuplicateDetectionAgentOutput(
            result=DuplicateDetectionResult(
                classification="insufficient_evidence",
                analysis_summary=reason,
                thresholds_used={
                    "likely_duplicate": self.likely_duplicate_threshold,
                    "related_issue": self.related_issue_threshold,
                },
            ),
            duration=duration,
            timestamp=datetime.utcnow().isoformat(),
            status="insufficient_evidence",
        ).dict()
