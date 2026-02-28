#!/usr/bin/env python3
"""
Code Quality Check Runner
Runs various code quality checks and static analysis tools.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, description, continue_on_error=True):
    """Run a command and handle errors."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print('='*60)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print("✅ PASSED")
        if result.stdout:
            print("STDOUT:")
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print("❌ FAILED")
        if e.stdout:
            print("STDOUT:")
            print(e.stdout)
        if e.stderr:
            print("STDERR:")
            print(e.stderr)
        
        if not continue_on_error:
            sys.exit(1)
        return False
    except FileNotFoundError:
        print(f"❌ Tool not found. Install with: pip install {cmd[0]}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Run code quality checks")
    parser.add_argument("--fail-fast", action="store_true", 
                       help="Stop on first failure")
    parser.add_argument("--include", nargs="*", 
                       choices=["tests", "pylint", "flake8", "mypy", "black", "isort", "bandit"],
                       default=["tests", "pylint", "flake8", "mypy", "black", "isort", "bandit"],
                       help="Which checks to run")
    parser.add_argument("--exclude-dirs", nargs="*", 
                       default=["venv", ".venv", "__pycache__", ".git", "build", "dist"],
                       help="Directories to exclude")
    
    args = parser.parse_args()
    
    # Get project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    # Ensure tools are available
    tools_needed = {
        "pylint": "pylint",
        "flake8": "flake8", 
        "mypy": "mypy",
        "black": "black",
        "isort": "isort",
        "bandit": "bandit[toml]"
    }
    
    results = {}
    continue_on_error = not args.fail_fast
    
    # 1. Run our custom code quality tests
    if "tests" in args.include:
        results["code_quality_tests"] = run_command(
            ["python", "-m", "pytest", "tests/test_code_quality.py", "-v"],
            "Custom Code Quality Tests",
            continue_on_error
        )
    
    # 2. Run pylint
    if "pylint" in args.include:
        exclude_pattern = ",".join(args.exclude_dirs)
        results["pylint"] = run_command(
            ["python", "-m", "pylint", "--ignore=" + exclude_pattern, "app_modules", "rewriter", "style_analyzer", "rules", "ambiguity", "src"],
            "Pylint Static Analysis",
            continue_on_error
        )
    
    # 3. Run flake8
    if "flake8" in args.include:
        results["flake8"] = run_command(
            ["python", "-m", "flake8", ".", "--exclude=" + ",".join(args.exclude_dirs)],
            "Flake8 Style Check",
            continue_on_error
        )
    
    # 4. Run mypy
    if "mypy" in args.include:
        results["mypy"] = run_command(
            ["python", "-m", "mypy", "app_modules", "rewriter", "style_analyzer", "rules", "ambiguity", "src"],
            "MyPy Type Checking",
            continue_on_error
        )
    
    # 5. Run black (check only)
    if "black" in args.include:
        results["black"] = run_command(
            ["python", "-m", "black", "--check", "--diff", "."],
            "Black Code Formatting Check",
            continue_on_error
        )
    
    # 6. Run isort (check only)
    if "isort" in args.include:
        results["isort"] = run_command(
            ["python", "-m", "isort", "--check-only", "--diff", "."],
            "Import Sorting Check",
            continue_on_error
        )
    
    # 7. Run bandit security check
    if "bandit" in args.include:
        results["bandit"] = run_command(
            ["python", "-m", "bandit", "-r", ".", "-f", "json", "--exclude", ",".join(args.exclude_dirs)],
            "Bandit Security Analysis",
            continue_on_error
        )
    
    # Summary
    print(f"\n{'='*60}")
    print("QUALITY CHECK SUMMARY")
    print('='*60)
    
    passed = 0
    failed = 0
    
    for check, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{check:25} {status}")
        if success:
            passed += 1
        else:
            failed += 1
    
    print(f"\nTotal: {passed + failed}, Passed: {passed}, Failed: {failed}")
    
    if failed > 0:
        print(f"\n⚠️  {failed} checks failed. Review output above for details.")
        if not continue_on_error:
            sys.exit(1)
    else:
        print("\n🎉 All quality checks passed!")


if __name__ == "__main__":
    main() 