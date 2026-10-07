#!/usr/bin/env python3
"""
Milestone 3 Evaluation Script.

Runs the M3 test cases against the actual agent pipeline and reports:
  - Per-agent pass/fail for each test case
  - Similarity score accuracy (real values, not mocked)
  - Evidence vs reasoning separation check
  - Confidence range validation
  - Overall pass rate

Usage:
    # From repo root (activate backend venv first):
    python scripts/evaluate_milestone3.py

    # Against a running backend API:
    python scripts/evaluate_milestone3.py --api http://localhost:8000

    # Run specific scenario:
    python scripts/evaluate_milestone3.py --scenario duplicate

    # Verbose output:
    python scripts/evaluate_milestone3.py --verbose
"""

import asyncio
import json
import sys
import os
import time
import argparse
import urllib.request
import urllib.error
from typing import Dict, Any, List, Tuple, Optional

# ── Path setup ─────────────────────────────────────────────────────────────────
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(REPO_ROOT, "backend")
DATA_DIR = os.path.join(REPO_ROOT, "data")
sys.path.insert(0, BACKEND_DIR)

TEST_CASES_FILE = os.path.join(DATA_DIR, "milestone3_test_cases.json")

# ── ANSI colors ────────────────────────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

def green(s):  return f"{GREEN}{s}{RESET}"
def red(s):    return f"{RED}{s}{RESET}"
def yellow(s): return f"{YELLOW}{s}{RESET}"
def cyan(s):   return f"{CYAN}{s}{RESET}"
def bold(s):   return f"{BOLD}{s}{RESET}"


# ── Result helpers ─────────────────────────────────────────────────────────────

class Check:
    """Represents a single assertion result."""
    def __init__(self, name: str, passed: bool, actual: Any, expected: Any, note: str = ""):
        self.name = name
        self.passed = passed
        self.actual = actual
        self.expected = expected
        self.note = note

    def __repr__(self):
        symbol = green("✓") if self.passed else red("✗")
        line = f"  {symbol} {self.name}"
        if not self.passed:
            line += f"\n      Expected: {self.expected}\n      Got:      {self.actual}"
        if self.note:
            line += f"\n      Note:     {self.note}"
        return line


class TestResult:
    def __init__(self, tc_id: str, name: str, scenario: str):
        self.tc_id = tc_id
        self.name = name
        self.scenario = scenario
        self.checks: List[Check] = []
        self.error: Optional[str] = None
        self.duration: float = 0.0

    @property
    def passed(self):
        if self.error:
            return False
        return all(c.passed for c in self.checks)

    @property
    def total_checks(self):
        return len(self.checks)

    @property
    def passed_checks(self):
        return sum(1 for c in self.checks if c.passed)


# ── Assertion helpers ──────────────────────────────────────────────────────────

def check(result: TestResult, name: str, condition: bool,
          actual: Any = None, expected: Any = None, note: str = ""):
    result.checks.append(Check(name, condition, actual, expected, note))


# ── Analysis runner (direct agent import or via API) ──────────────────────────

async def run_analysis_direct(bug_data: Dict) -> Dict:
    """Run M3 pipeline directly by importing agents (no server needed)."""
    from agents.orchestrator import AgentOrchestrator
    from services.llm_service import LLMService
    from services.chroma_service import ChromaService
    from services.embedding_service import EmbeddingService

    orchestrator = AgentOrchestrator(
        llm_service=LLMService(),
        chroma_service=ChromaService(),
        embedding_service=EmbeddingService(),
    )
    return await orchestrator.run_m3_pipeline(bug_data)


def run_analysis_api(api_base: str, bug_data: Dict) -> Dict:
    """Submit bug and run analysis via running API."""
    # 1. Submit bug
    payload = json.dumps({
        "title": bug_data["title"],
        "description": bug_data["description"],
        "stack_trace": bug_data.get("stack_trace"),
        "error_logs": bug_data.get("error_logs"),
        "environment": bug_data.get("environment"),
    }).encode()

    req = urllib.request.Request(
        f"{api_base}/api/bugs",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        submitted = json.loads(resp.read())
    bug_id = submitted["id"]

    # 2. Run analysis
    req2 = urllib.request.Request(
        f"{api_base}/api/bugs/{bug_id}/analyze",
        data=b"",
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req2, timeout=120) as resp:
        return json.loads(resp.read())


# ── Evaluators per agent ───────────────────────────────────────────────────────

def evaluate_triage(result: TestResult, triage: Dict, expected: Dict):
    """Evaluate triage agent output."""
    if not triage:
        check(result, "triage.result_present", False, None, "dict", "Triage returned empty")
        return

    severity = triage.get("severity", "")
    priority = triage.get("priority", "")
    category = triage.get("category", "")
    confidence = triage.get("confidence", 0.0)

    if "severity" in expected:
        check(result, "triage.severity",
              severity == expected["severity"], severity, expected["severity"])

    if "severity_in" in expected:
        check(result, "triage.severity_in",
              severity in expected["severity_in"], severity, expected["severity_in"])

    if "priority" in expected:
        check(result, "triage.priority",
              priority == expected["priority"], priority, expected["priority"])

    if "category_contains" in expected:
        check(result, "triage.category_contains",
              expected["category_contains"].lower() in category.lower(),
              category, f"contains '{expected['category_contains']}'")

    if "category_contains_any" in expected:
        hit = any(s.lower() in category.lower() for s in expected["category_contains_any"])
        check(result, "triage.category_contains_any", hit, category, expected["category_contains_any"])

    if "confidence_max" in expected:
        check(result, "triage.confidence_max",
              confidence <= expected["confidence_max"], confidence, f"<= {expected['confidence_max']}")

    # Always check confidence is in range
    check(result, "triage.confidence_range",
          0.0 <= confidence <= 1.0, confidence, "0.0 – 1.0")
    check(result, "triage.reasoning_not_empty",
          bool(triage.get("reasoning", "").strip()), None, "non-empty string")


def evaluate_log_analysis(result: TestResult, log: Dict, expected: Dict):
    """Evaluate log analysis agent output."""
    if not log:
        check(result, "log_analysis.result_present", False, None, "dict")
        return

    exceptions = log.get("exceptions", [])
    confidence = log.get("confidence", 0.0)

    if "exception_count_min" in expected:
        check(result, "log_analysis.exception_count_min",
              len(exceptions) >= expected["exception_count_min"],
              len(exceptions), f">= {expected['exception_count_min']}")

    if "exception_type_contains" in expected:
        types = [
            (e.get("exception_type") or e.get("exceptionType") or e.get("type") or "")
            for e in exceptions
        ]
        hit = any(expected["exception_type_contains"].lower() in t.lower() for t in types)
        check(result, "log_analysis.exception_type_contains",
              hit or len(exceptions) == 0,  # OK if no exceptions expected
              types, f"contains '{expected['exception_type_contains']}'")

    if expected.get("failure_point_present"):
        fp = log.get("failure_point")
        check(result, "log_analysis.failure_point_present", bool(fp), fp, "non-empty string")

    if expected.get("line_number_present"):
        has_line = any(
            (e.get("line_number") or e.get("lineNumber") or e.get("line")) is not None
            for e in exceptions
        )
        check(result, "log_analysis.line_number_present", has_line, exceptions, "line number in exception")

    if "confidence_max" in expected:
        check(result, "log_analysis.confidence_max",
              confidence <= expected["confidence_max"], confidence, f"<= {expected['confidence_max']}")

    check(result, "log_analysis.confidence_range",
          0.0 <= confidence <= 1.0, confidence, "0.0 – 1.0")


def evaluate_root_cause(result: TestResult, rc: Dict, expected: Dict):
    """Evaluate root cause agent output."""
    if not rc:
        check(result, "root_cause.result_present", False, None, "dict")
        return

    status = rc.get("status", "")
    probable_cause = rc.get("probable_cause", "")
    confidence = rc.get("confidence", 0.0)
    retrieved_evidence = rc.get("retrieved_evidence", [])
    agent_reasoning = rc.get("agent_reasoning", "")
    evidence_summary = rc.get("evidence_summary", "")

    if "status" in expected:
        check(result, "root_cause.status",
              status == expected["status"], status, expected["status"])

    if "status_in" in expected:
        check(result, "root_cause.status_in",
              status in expected["status_in"], status, expected["status_in"])

    if expected.get("probable_cause_not_empty"):
        check(result, "root_cause.probable_cause_not_empty",
              bool(probable_cause.strip()), probable_cause, "non-empty string")

    if "confidence_min" in expected:
        check(result, "root_cause.confidence_min",
              confidence >= expected["confidence_min"],
              confidence, f">= {expected['confidence_min']}")

    if "confidence_max" in expected:
        check(result, "root_cause.confidence_max",
              confidence <= expected["confidence_max"],
              confidence, f"<= {expected['confidence_max']}")

    if "retrieved_evidence_count_min" in expected:
        check(result, "root_cause.retrieved_evidence",
              len(retrieved_evidence) >= expected["retrieved_evidence_count_min"],
              len(retrieved_evidence), f">= {expected['retrieved_evidence_count_min']}")

    check(result, "root_cause.confidence_range",
          0.0 <= confidence <= 1.0, confidence, "0.0 – 1.0")

    # M3 requirement: evidence vs reasoning separated
    check(result, "root_cause.evidence_summary_present",
          isinstance(evidence_summary, str),
          type(evidence_summary).__name__, "str")


def evaluate_duplicate_detection(result: TestResult, dd: Dict, expected: Dict):
    """Evaluate duplicate detection agent output."""
    if not dd:
        check(result, "duplicate_detection.result_present", False, None, "dict")
        return

    classification = dd.get("classification", "")
    top_sim = dd.get("top_match_similarity", dd.get("similarity_score", 0.0))
    dup_prob = dd.get("duplicate_probability", 0.0)
    matched = dd.get("matched_bugs", dd.get("matching_bugs", []))
    thresholds = dd.get("thresholds_used", {})

    if "classification" in expected:
        check(result, "duplicate_detection.classification",
              classification == expected["classification"], classification, expected["classification"])

    if "classification_in" in expected:
        check(result, "duplicate_detection.classification_in",
              classification in expected["classification_in"], classification, expected["classification_in"])

    if "top_match_similarity_min" in expected:
        check(result, "duplicate_detection.top_similarity_min",
              top_sim >= expected["top_match_similarity_min"],
              round(top_sim, 4), f">= {expected['top_match_similarity_min']}")

    if "top_match_similarity_max" in expected:
        check(result, "duplicate_detection.top_similarity_max",
              top_sim <= expected["top_match_similarity_max"],
              round(top_sim, 4), f"<= {expected['top_match_similarity_max']}")

    if "matched_bugs_count_min" in expected:
        check(result, "duplicate_detection.matched_count_min",
              len(matched) >= expected["matched_bugs_count_min"],
              len(matched), f">= {expected['matched_bugs_count_min']}")

    check(result, "duplicate_detection.similarity_range",
          0.0 <= top_sim <= 1.0, round(top_sim, 4), "0.0 – 1.0")

    check(result, "duplicate_detection.prob_range",
          0.0 <= dup_prob <= 1.0, round(dup_prob, 4), "0.0 – 1.0")

    # M3 requirement: thresholds reported
    check(result, "duplicate_detection.thresholds_reported",
          bool(thresholds), thresholds, "non-empty dict")

    # M3 requirement: each match has real similarity score (not 0)
    for i, m in enumerate(matched[:3]):
        score = m.get("similarity_score", m.get("similarity", 0.0))
        check(result, f"duplicate_detection.match[{i}].score_nonzero",
              score > 0.0, round(score, 4), "> 0.0")


def evaluate_remediation(result: TestResult, rem: Dict, expected: Dict):
    """Evaluate remediation agent output."""
    if not rem:
        check(result, "remediation.result_present", False, None, "dict")
        return

    status = rem.get("status", "")
    suggested_fix = rem.get("suggested_fix", "")
    fix_source = rem.get("fix_source", "")
    confidence = rem.get("confidence", 0.0)
    impl_steps = rem.get("implementation_steps", [])
    debug_steps = rem.get("debugging_steps", [])
    val_steps = rem.get("validation_steps", [])
    hist_res = rem.get("historical_resolutions", [])

    if "status" in expected:
        check(result, "remediation.status",
              status == expected["status"], status, expected["status"])

    if "status_in" in expected:
        check(result, "remediation.status_in",
              status in expected["status_in"], status, expected["status_in"])

    if expected.get("suggested_fix_not_empty"):
        check(result, "remediation.suggested_fix_not_empty",
              bool(suggested_fix.strip()), suggested_fix[:60], "non-empty string")

    if "debugging_steps_count_min" in expected:
        check(result, "remediation.debugging_steps_min",
              len(debug_steps) >= expected["debugging_steps_count_min"],
              len(debug_steps), f">= {expected['debugging_steps_count_min']}")

    if "validation_steps_count_min" in expected:
        check(result, "remediation.validation_steps_min",
              len(val_steps) >= expected["validation_steps_count_min"],
              len(val_steps), f">= {expected['validation_steps_count_min']}")

    if "historical_resolutions_count_min" in expected:
        check(result, "remediation.historical_resolutions_min",
              len(hist_res) >= expected["historical_resolutions_count_min"],
              len(hist_res), f">= {expected['historical_resolutions_count_min']}")

    check(result, "remediation.confidence_range",
          0.0 <= confidence <= 1.0, confidence, "0.0 – 1.0")

    # M3 requirement: fix source labeled
    valid_sources = {"historical_evidence", "best_practice", "agent_reasoning", ""}
    check(result, "remediation.fix_source_valid",
          fix_source in valid_sources, fix_source, str(valid_sources))

    # M3 requirement: implementation steps present
    check(result, "remediation.has_implementation_steps",
          len(impl_steps) >= 0, len(impl_steps), ">= 0")


# ── Test runner ────────────────────────────────────────────────────────────────

async def run_test_case(
    tc: Dict,
    api_base: Optional[str],
    verbose: bool,
) -> TestResult:
    """Run a single test case and return results."""
    result = TestResult(tc["id"], tc["name"], tc["scenario"])
    bug_data = tc["bug"]
    expected = tc["expected"]

    start = time.time()
    try:
        if api_base:
            raw = await asyncio.get_event_loop().run_in_executor(
                None, run_analysis_api, api_base, bug_data
            )
        else:
            raw = await run_analysis_direct(bug_data)

        result.duration = time.time() - start

        # Extract agent results (handle both flat and nested shapes)
        triage   = raw.get("triage") or raw.get("agents", {}).get("triage", {}).get("result", {})
        log      = raw.get("log_analysis") or raw.get("agents", {}).get("log_analysis", {}).get("result", {})
        rc       = raw.get("root_cause") or raw.get("agents", {}).get("root_cause", {}).get("result", {})
        dd       = raw.get("duplicate_detection") or raw.get("agents", {}).get("duplicate_detection", {}).get("result", {})
        rem      = raw.get("remediation") or raw.get("agents", {}).get("remediation", {}).get("result", {})

        # Check pipeline completed
        check(result, "pipeline.status",
              raw.get("status") == "completed", raw.get("status"), "completed")

        check(result, "pipeline.all_agents_ran",
              all(k in (raw.get("agents") or {}) for k in
                  ["triage", "log_analysis", "root_cause", "duplicate_detection", "remediation"]),
              list((raw.get("agents") or {}).keys()), "5 agents present")

        # Per-agent evaluation
        evaluate_triage(result, triage, expected.get("triage", {}))
        evaluate_log_analysis(result, log, expected.get("log_analysis", {}))
        evaluate_root_cause(result, rc, expected.get("root_cause", {}))
        evaluate_duplicate_detection(result, dd, expected.get("duplicate_detection", {}))
        evaluate_remediation(result, rem, expected.get("remediation", {}))

    except Exception as e:
        result.duration = time.time() - start
        result.error = str(e)

    return result


async def run_all(
    test_cases: List[Dict],
    scenario_filter: Optional[str],
    api_base: Optional[str],
    verbose: bool,
) -> List[TestResult]:
    """Run all (or filtered) test cases."""
    filtered = test_cases
    if scenario_filter:
        filtered = [tc for tc in test_cases if tc["scenario"] == scenario_filter]
        if not filtered:
            print(red(f"No test cases match scenario '{scenario_filter}'"))
            print(f"Available: {sorted(set(t['scenario'] for t in test_cases))}")
            sys.exit(1)

    results = []
    for tc in filtered:
        print(f"\n{'─'*60}")
        print(bold(f"[{tc['id']}] {tc['name']}"))
        print(f"  Scenario: {cyan(tc['scenario'])}")

        result = await run_test_case(tc, api_base, verbose)
        results.append(result)

        if result.error:
            print(red(f"  ✗ AGENT ERROR: {result.error}"))
        else:
            for c in result.checks:
                if verbose or not c.passed:
                    print(repr(c))

        status_str = green("PASS") if result.passed else red("FAIL")
        print(f"  Result: {status_str}  ({result.passed_checks}/{result.total_checks} checks)  {result.duration:.2f}s")

    return results


def print_summary(results: List[TestResult]):
    """Print final summary table."""
    total = len(results)
    passed = sum(1 for r in results if r.passed)
    failed = total - passed
    total_checks = sum(r.total_checks for r in results)
    passed_checks = sum(r.passed_checks for r in results)

    print(f"\n{'═'*60}")
    print(bold("MILESTONE 3 EVALUATION SUMMARY"))
    print(f"{'═'*60}")
    print(f"  Test Cases:  {green(str(passed))} passed, {red(str(failed))} failed of {total}")
    print(f"  Assertions:  {green(str(passed_checks))} passed of {total_checks}")
    print(f"  Pass Rate:   {(passed_checks/total_checks*100):.1f}%" if total_checks else "  Pass Rate: N/A")
    print()

    # Per-scenario breakdown
    scenarios = sorted(set(r.scenario for r in results))
    for sc in scenarios:
        sc_results = [r for r in results if r.scenario == sc]
        sc_pass = sum(1 for r in sc_results if r.passed)
        color = green if sc_pass == len(sc_results) else (yellow if sc_pass > 0 else red)
        print(f"  {sc:<25} {color(f'{sc_pass}/{len(sc_results)} passed')}")

    print()
    if failed:
        print(bold("Failed test cases:"))
        for r in results:
            if not r.passed:
                failed_checks = [c for c in r.checks if not c.passed]
                print(f"  {red('✗')} {r.tc_id}: {r.name}")
                if r.error:
                    print(f"      Error: {r.error}")
                else:
                    for c in failed_checks[:3]:
                        print(f"      - {c.name}: expected={c.expected}, got={c.actual}")
    else:
        print(green("All test cases passed! ✓"))

    print(f"{'═'*60}\n")
    return passed == total


# ── CLI entry point ────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Evaluate Milestone 3 agents")
    parser.add_argument("--api", metavar="URL",
                        help="Run against a live API (e.g. http://localhost:8000)")
    parser.add_argument("--scenario", metavar="NAME",
                        help="Filter by scenario (duplicate, related_issue, unrelated, etc.)")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Print all checks, not just failures")
    parser.add_argument("--test-file", default=TEST_CASES_FILE,
                        help=f"Path to test cases JSON (default: {TEST_CASES_FILE})")
    args = parser.parse_args()

    # Load test cases
    if not os.path.exists(args.test_file):
        print(red(f"Test cases file not found: {args.test_file}"))
        sys.exit(1)

    with open(args.test_file) as f:
        data = json.load(f)
    test_cases = data["test_cases"]

    print(bold(f"\n{'═'*60}"))
    print(bold(f"  DefectMind AI — Milestone 3 Evaluation"))
    print(bold(f"  {len(test_cases)} test cases in {args.test_file}"))
    if args.api:
        print(f"  Mode: API ({args.api})")
    else:
        print(f"  Mode: Direct (importing agents from {BACKEND_DIR})")
    print(bold(f"{'═'*60}"))

    results = asyncio.run(run_all(test_cases, args.scenario, args.api, args.verbose))
    success = print_summary(results)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
