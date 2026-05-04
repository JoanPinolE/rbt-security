#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_tests.py  --  Master Test Runner for RBT Security
======================================================

Run with PYTHON, not pytest:
    python run_tests.py              # default: security + advanced + integration
    python run_tests.py --all        # every suite
    python run_tests.py --all --no-soak   # every suite, skip 2-min soak
    python run_tests.py --load       # load & performance only
    python run_tests.py --pentest    # penetration only
    python run_tests.py --e2e        # end-to-end only
    python run_tests.py --no-api     # unit + ai without Docker
    python run_tests.py --all --report    # all + HTML reports in reports/
    python run_tests.py --grafana    # generate Grafana traffic

WRONG: pytest run_tests.py   (has no test_ functions -- 0 items collected)
RIGHT: python run_tests.py
"""

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

BASE       = "http://localhost:8000"
PROMETHEUS = "http://localhost:9090"
GRAFANA    = "http://localhost:3000"

# Force UTF-8 output on Windows so print() works everywhere
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    # Enable ANSI color support in Windows 10+ console
    try:
        import ctypes
        ctypes.windll.kernel32.SetConsoleMode(
            ctypes.windll.kernel32.GetStdHandle(-11), 7)
    except Exception:
        pass

G  = "\033[92m"   # green
R  = "\033[91m"   # red
Y  = "\033[93m"   # yellow
C  = "\033[96m"   # cyan
B  = "\033[1m"    # bold
RS = "\033[0m"    # reset


# =====================================================================
# SERVICE CHECKS
# =====================================================================
def reachable(url):
    try:
        urllib.request.urlopen(url, timeout=4)
        return True
    except Exception:
        return False


def check_services():
    print(f"\n{C}Checking services...{RS}")
    api  = reachable(f"{BASE}/")
    prom = reachable(f"{PROMETHEUS}/-/healthy")
    graf = reachable(f"{GRAFANA}/api/health")

    tag = lambda ok: f"{G}UP {RS}" if ok else f"{R}-- {RS}"
    print(f"  {tag(api)}  FastAPI    http://localhost:8000")
    print(f"  {tag(prom)}  Prometheus http://localhost:9090")
    print(f"  {tag(graf)}  Grafana    http://localhost:3000")

    if api:
        try:
            d = json.loads(urllib.request.urlopen(f"{BASE}/status", timeout=4).read())
            ml = d.get("ml_model_loaded", False)
            ml_tag = f"{G}loaded{RS}" if ml else f"{Y}NOT loaded -- docker compose up --build -d{RS}"
            print(f"  {'OK ' if ml else 'WRN'}  ML Model   {ml_tag}")
        except Exception:
            pass
    print()
    return api, prom, graf


# =====================================================================
# PYTEST RUNNER
# =====================================================================
def run_pytest(paths, label, extra_args=None, report_name=None):
    print(f"\n{B}{C}{'=' * 60}{RS}")
    print(f"{B}  {label}{RS}")
    print(f"{B}{C}{'=' * 60}{RS}\n")

    cmd = [sys.executable, "-m", "pytest"] + paths + ["-v", "--tb=short"]

    if report_name:
        os.makedirs("reports", exist_ok=True)
        cmd += [f"--html=reports/{report_name}.html", "--self-contained-html"]

    if extra_args:
        cmd += extra_args

    print(f"  {C}CMD:{RS} {' '.join(cmd)}\n")
    return subprocess.run(cmd).returncode == 0


# =====================================================================
# MAIN
# =====================================================================
def main():
    parser = argparse.ArgumentParser(
        prog="python run_tests.py",
        description="RBT Security -- Master Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py                   (default: security + advanced + integration)
  python run_tests.py --all             (every suite)
  python run_tests.py --all --no-soak   (skip the 2-min soak test)
  python run_tests.py --load --report   (load tests + HTML report)
  python run_tests.py --pentest         (penetration tests only)
  python run_tests.py --e2e             (end-to-end only)
  python run_tests.py --no-api          (unit + ai, no Docker needed)

WRONG: pytest run_tests.py
RIGHT: python run_tests.py
        """,
    )

    # -- Suite flags --
    parser.add_argument("--unit",        action="store_true", help="Unit tests (no API)")
    parser.add_argument("--security",    action="store_true", help="Security tests")
    parser.add_argument("--advanced",    action="store_true", help="Advanced tests")
    parser.add_argument("--integration", action="store_true", help="Integration tests")
    parser.add_argument("--load",        action="store_true", help="Load & performance")
    parser.add_argument("--pentest",     action="store_true", help="Penetration tests")
    parser.add_argument("--e2e",         action="store_true", help="End-to-end tests")
    parser.add_argument("--scraping",    action="store_true", help="Scraping & metrics")
    parser.add_argument("--ai",          action="store_true", help="AI/ML tests")

    # -- Presets --
    parser.add_argument("--all",    action="store_true", help="All API-dependent suites")
    parser.add_argument("--quick",  action="store_true", help="security + advanced + integration")
    parser.add_argument("--no-api", action="store_true", help="unit + ai (no Docker)")

    # -- Options --
    parser.add_argument("--no-soak", action="store_true",
                        help="Skip the 2-min soak test")
    parser.add_argument("--report",  action="store_true",
                        help="Generate HTML reports in reports/")
    parser.add_argument("--grafana", action="store_true",
                        help="Generate traffic to populate Grafana panels")

    args = parser.parse_args()

    print(f"\n{B}RBT Security -- Master Test Runner{RS}")
    print("-" * 60)
    print(f"  Python  : {sys.version.split()[0]}")
    print(f"  Platform: {sys.platform}")
    print(f"  Dir     : {Path.cwd()}")

    api_ok, prom_ok, graf_ok = check_services()

    # Default to --quick when nothing is selected
    nothing = not any([
        args.unit, args.security, args.advanced, args.integration,
        args.load, args.pentest, args.e2e, args.scraping, args.ai,
        args.all, args.quick, args.no_api, args.grafana,
    ])
    if nothing:
        print(f"{Y}No suite selected -- running --quick{RS}")
        args.quick = True

    # Must have API for most suites
    if not api_ok and not args.no_api and not args.unit and not args.ai:
        print(f"{R}API not reachable at http://localhost:8000{RS}")
        print("  Start with: docker compose up -d")
        print("  Or run:     python run_tests.py --no-api")
        sys.exit(1)

    results = {}
    t0 = time.time()

    # --no-soak skips the 2-min sustained load test by its method name
    no_soak = ["-k", "not sustained_2_minutes"] if args.no_soak else []

    def suite(flag, paths, label, extra=None, report=None):
        if not flag:
            return
        # Skip missing files gracefully
        found = [p for p in paths if Path(p.split("::")[0]).exists()]
        if not found:
            print(f"{Y}  SKIP  {label} -- files not found{RS}")
            results[label] = None
            return
        # Check API availability
        needs_api = not any("unit" in p or "ai" in p for p in paths)
        if needs_api and not api_ok:
            print(f"{Y}  SKIP  {label} -- API not available{RS}")
            results[label] = None
            return
        rep = report if args.report else None
        results[label] = run_pytest(
            found, label,
            extra_args=(extra or []) + no_soak,
            report_name=rep,
        )

    # -- Unit (no API) -----------------------------------------------------
    unit_files = [p for p in [
        "tests/test_unit.py", "tests/test_unit_deep.py"
    ] if Path(p).exists()]
    suite(args.unit or args.all or args.no_api,
          unit_files or ["tests/test_unit.py"],
          "UNIT TESTS (no API required)",
          report="unit")

    # -- AI (mostly no API) ------------------------------------------------
    ai_extra = ["-k", "not live"] if args.no_api else []
    suite(args.ai or args.all or args.no_api,
          ["tests/test_ai.py"],
          "AI/ML TESTS -- quality, robustness, fairness, drift",
          extra=ai_extra, report="ai")

    # -- Security ----------------------------------------------------------
    suite(args.security or args.all or args.quick,
          ["tests/test_security.py"],
          "SECURITY TESTS -- Risk Score, auth, false positives, ML",
          report="security")

    # -- Advanced ----------------------------------------------------------
    suite(args.advanced or args.all or args.quick,
          ["tests/test_advanced.py"],
          "ADVANCED TESTS -- API contract, chaos, concurrency, boundary",
          report="advanced")

    # -- Integration -------------------------------------------------------
    suite(args.integration or args.all or args.quick,
          ["tests/test_integration.py"],
          "INTEGRATION TESTS -- FastAPI + Redis + ML + Prometheus",
          report="integration")

    # -- Scraping ----------------------------------------------------------
    suite(args.scraping or args.all,
          ["tests/test_scraping.py"],
          "SCRAPING TESTS -- /metrics format, labels, values, Prometheus",
          report="scraping")

    # -- Penetration -------------------------------------------------------
    suite(args.pentest or args.all,
          ["tests/test_penetration.py"],
          "PENETRATION TESTS -- SQL, XSS, brute force, evasion",
          extra=["-s"], report="pentest")

    # -- Load --------------------------------------------------------------
    suite(args.load or args.all,
          ["tests/test_load.py"],
          "LOAD TESTS -- performance, concurrency, spike, soak",
          extra=["-s"], report="load")

    # -- E2E ---------------------------------------------------------------
    suite(args.e2e or args.all,
          ["tests/test_e2e.py"],
          "E2E TESTS -- full journeys, Prometheus, Grafana",
          extra=["-s"], report="e2e")

    # -- Grafana traffic generation ----------------------------------------
    if args.grafana and api_ok and Path("tests/test_security.py").exists():
        print(f"\n{C}Generating traffic for Grafana...{RS}")
        run_pytest(
            ["tests/test_security.py::TestLoadGeneration"],
            "GRAFANA DATA -- mixed traffic to populate panels",
            extra=["-s"],
        )
        print(f"  Open: {C}http://localhost:3000{RS}")

    # -- Summary -----------------------------------------------------------
    elapsed = time.time() - t0
    print(f"\n{'=' * 60}")
    print(f"{B}  SUMMARY  ({elapsed:.0f}s){RS}")
    print(f"{'=' * 60}")

    all_passed = True
    for name, passed in results.items():
        if passed is None:
            print(f"  {Y}SKIP{RS}  {name}")
        elif passed:
            print(f"  {G}PASS{RS}  {name}")
        else:
            print(f"  {R}FAIL{RS}  {name}")
            all_passed = False

    if results:
        print()
        if args.report:
            print(f"  Reports : {C}reports/{RS}")
        print(f"  Grafana : {C}http://localhost:3000{RS}")
        print(f"  Prometheus: {C}http://localhost:9090{RS}")
    print()

    if not results:
        print(f"{Y}No suites ran. Use --help to see options.{RS}")
    elif all_passed:
        print(f"{G}{B}All suites passed.{RS}")
    else:
        print(f"{R}Some suites failed -- review output above.{RS}")
        sys.exit(1)


if __name__ == "__main__":
    main()
