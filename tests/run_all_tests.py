"""
Master Test Runner for Nyro AI Clip Factory (Phases 1 - 10)
"""
import sys
import subprocess
from pathlib import Path

def run_suite():
    tests = [
        "tests/test_phase1.py",
        "tests/test_phase2.py",
        "tests/test_phase3.py",
        "tests/test_phase4.py",
        "tests/test_phase5.py",
        "tests/test_phase6.py",
        "tests/test_phase7.py",
        "tests/test_phase8.py",
        "tests/test_phase9.py",
        "tests/test_phase10.py",
    ]

    print("=" * 65, flush=True)
    print("NYRO AI CLIP FACTORY — MASTER TEST SUITE (PHASES 1 TO 10)", flush=True)
    print("=" * 65, flush=True)

    passed = 0
    for t in tests:
        print(f"\n>> Running: {t}...", flush=True)
        res = subprocess.run([sys.executable, t], capture_output=True, text=True)
        if res.returncode == 0:
            print(f"   ✓ {t} PASSED", flush=True)
            passed += 1
        else:
            print(f"   ✕ {t} FAILED", flush=True)
            print("--- STDOUT ---", flush=True)
            print(res.stdout, flush=True)
            print("--- STDERR ---", flush=True)
            print(res.stderr, flush=True)

    print("\n" + "=" * 65, flush=True)
    print(f"TOTAL RESULT: {passed}/{len(tests)} TEST SUITES PASSED", flush=True)
    print("=" * 65, flush=True)

    if passed != len(tests):
        sys.exit(1)

if __name__ == "__main__":
    run_suite()
