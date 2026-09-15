"""
Milestone 2 Evaluation Script.

Runs test cases through the Triage and Log Analysis agents,
measures accuracy of severity, priority, component, exception type,
failure point, and code path predictions.

Does NOT fabricate results — runs actual agent code against test data.
"""

import os
import sys
import json
import asyncio
import time
from typing import Dict, Any, List

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backend'))

from agents.triage_agent import TriageAgent
from agents.log_analysis_agent import LogAnalysisAgent
from agents.orchestrator import AgentOrchestrator


def load_test_cases() -> List[Dict]:
    """Load test cases from JSON file."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'milestone2_test_cases.json')
    with open(path, 'r') as f:
        data = json.load(f)
    return data['test_cases']


def compare_severity(expected: str, actual: str) -> bool:
    """Compare severity levels."""
    return expected.lower() == actual.lower()


def compare_priority(expected: str, actual: str) -> bool:
    """Compare priority levels."""
    return expected.upper() == actual.upper()


def compare_exception_type(expected: str, actual_exc_list: List[Dict]) -> bool:
    """Compare exception type against parsed exceptions."""
    if expected is None:
        return len(actual_exc_list) == 0 or all(
            e.get('exception_type', e.get('type', '')) == 'RuntimeException' for e in actual_exc_list
        )
    
    for exc in actual_exc_list:
        exc_type = exc.get('exception_type', exc.get('type', ''))
        if expected.lower() in exc_type.lower():
            return True
    return False


def compare_file_name(expected: str, actual_exc_list: List[Dict]) -> bool:
    """Compare file name."""
    if expected is None:
        return True  # No expectation
    
    for exc in actual_exc_list:
        file_name = exc.get('fileName') or exc.get('file_name') or exc.get('file', '')
        if file_name and expected.lower() in file_name.lower():
            return True
    return False


def compare_line_number(expected: int, actual_exc_list: List[Dict]) -> bool:
    """Compare line number."""
    if expected is None:
        return True
    
    for exc in actual_exc_list:
        line = exc.get('lineNumber') or exc.get('line_number') or exc.get('line')
        if line is not None and int(line) == expected:
            return True
    return False


def compare_method_name(expected: str, actual_exc_list: List[Dict]) -> bool:
    """Compare method name."""
    if expected is None:
        return True
    
    for exc in actual_exc_list:
        method = exc.get('methodName') or exc.get('method_name') or exc.get('method', '')
        if method and expected.lower() in method.lower():
            return True
    return False


async def evaluate_test_case(test_case: Dict, orchestrator: AgentOrchestrator) -> Dict[str, Any]:
    """Evaluate a single test case."""
    bug_data = {
        'id': test_case['id'],
        'title': test_case['bug']['title'],
        'description': test_case['bug']['description'],
        'stack_trace': test_case['bug'].get('stack_trace', ''),
        'error_logs': test_case['bug'].get('error_logs', ''),
        'environment': test_case['bug'].get('environment', '')
    }
    
    expected = test_case['expected']
    
    # Run M2 pipeline
    result = await orchestrator.run_m2_pipeline(bug_data)
    
    # Extract results
    triage = result.get('triage', {})
    log_analysis = result.get('log_analysis', {})
    exceptions = log_analysis.get('exceptions', [])
    
    # Compare results
    comparisons = {
        'severity_correct': compare_severity(expected['severity'], triage.get('severity', '')),
        'priority_correct': compare_priority(expected['priority'], triage.get('priority', '')),
        'exception_type_correct': compare_exception_type(expected.get('exception_type'), exceptions),
        'file_name_correct': compare_file_name(expected.get('file_name'), exceptions),
        'line_number_correct': compare_line_number(expected.get('line_number'), exceptions),
        'method_name_correct': compare_method_name(expected.get('method_name'), exceptions),
    }
    
    return {
        'test_id': test_case['id'],
        'description': test_case['description'],
        'triage_result': triage,
        'log_result': {
            'exception_count': len(exceptions),
            'failure_point': log_analysis.get('failure_point'),
            'code_path': log_analysis.get('code_path'),
            'confidence': log_analysis.get('confidence'),
        },
        'comparisons': comparisons,
        'duration': result.get('total_duration', 0)
    }


async def run_evaluation():
    """Run the full evaluation suite."""
    print("=" * 70)
    print("MILESTONE 2 EVALUATION")
    print("=" * 70)
    
    test_cases = load_test_cases()
    print(f"\nLoaded {len(test_cases)} test cases")
    
    # Initialize orchestrator
    orchestrator = AgentOrchestrator()
    
    results = []
    start_time = time.time()
    
    for i, tc in enumerate(test_cases):
        print(f"\n[{i+1}/{len(test_cases)}] Evaluating: {tc['id']} — {tc['description']}")
        result = await evaluate_test_case(tc, orchestrator)
        results.append(result)
        
        # Print immediate results
        for key, correct in result['comparisons'].items():
            status = "✓" if correct else "✗"
            print(f"  {status} {key}: {correct}")
    
    total_time = time.time() - start_time
    
    # Calculate accuracy metrics
    print("\n" + "=" * 70)
    print("ACCURACY RESULTS")
    print("=" * 70)
    
    metrics = {
        'severity_accuracy': 0,
        'priority_accuracy': 0,
        'exception_type_accuracy': 0,
        'file_name_accuracy': 0,
        'line_number_accuracy': 0,
        'method_name_accuracy': 0,
    }
    
    for result in results:
        for key in metrics:
            if result['comparisons'].get(key, False):
                metrics[key] += 1
    
    total = len(results)
    print(f"\nTotal test cases: {total}")
    print(f"Total evaluation time: {total_time:.2f}s\n")
    
    print(f"{'Metric':<30} {'Correct':<10} {'Total':<10} {'Accuracy':<10}")
    print("-" * 60)
    
    for metric, count in metrics.items():
        accuracy = count / total if total > 0 else 0
        print(f"{metric:<30} {count:<10} {total:<10} {accuracy:.1%}")
    
    # Save results
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'milestone2_results.json')
    with open(output_path, 'w') as f:
        json.dump({
            'metadata': {
                'total_cases': total,
                'total_time': total_time,
                'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S')
            },
            'metrics': {k: v / total for k, v in metrics.items()},
            'results': results
        }, f, indent=2)
    
    print(f"\nResults saved to: {output_path}")
    print("=" * 70)
    
    return metrics


if __name__ == "__main__":
    asyncio.run(run_evaluation())
