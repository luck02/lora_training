"""
Quality check script for the LoRA training pipeline.

Enforces strict code quality standards:
- Linting with ruff
- Test coverage >= 80%
- McCabe complexity <= 15 per function
"""

import sys
import subprocess
import argparse
import re
from pathlib import Path
from typing import List, Optional

class QualityChecker:
    def __init__(self):
        self.errors = []
        self.config = None

    def parse_args(self):
        parser = argparse.ArgumentParser(description="Run quality checks on the codebase")
        parser.add_argument("--all", action="store_true", help="Check all Python files")
        parser.add_argument("--fix", action="store_true", help="Auto-fix issues")
        parser.add_argument("--check-only", action="store_true", help="Only check, don't fix")
        self.config = parser.parse_args()

        # If --fix is specified, --check-only is ignored
        if self.config.fix:
            self.config.check_only = False

    def get_files_to_check(self) -> List[Path]:
        """Detect Python files to check"""

        if self.config.all:
            # Check all Python files in scripts/ and tests/
            return list(Path("scripts").rglob("*.py")) + \
                   list(Path("tests").rglob("*.py"))

        # Use git to find modified files
        try:
            # Unstaged changes
            modified = subprocess.run(
                ["git", "diff", "--name-only", "HEAD"],
                capture_output=True, text=True, check=True
            ).stdout.splitlines()

            # Staged changes
            staged = subprocess.run(
                ["git", "diff", "--cached", "--name-only"],
                capture_output=True, text=True, check=True
            ).stdout.splitlines()

            # Filter for .py files
            py_files = [Path(f) for f in modified + staged if f.endswith(".py")]
            return list(set(py_files))

        except subprocess.CalledProcessError:
            # Not a git repo, fallback to all files
            return self.get_all_python_files()

    def get_all_python_files(self) -> List[Path]:
        """Get all Python files in scripts and tests directories"""
        return list(Path("scripts").rglob("*.py")) + \
               list(Path("tests").rglob("*.py"))

    def run_ruff_check(self, files: List[Path]) -> bool:
        """Run ruff linting"""
        if not files:
            return True

        cmd = ["ruff", "check"] + [str(f) for f in files]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            self.errors.append(("Linting", result.stdout))
            return False
        return True

    def run_ruff_fix(self, files: List[Path]):
        """Auto-fix linting issues"""
        if not files:
            return

        # Fix linting issues
        subprocess.run(["ruff", "check", "--fix"] + [str(f) for f in files],
                      capture_output=True)
        # Format code
        subprocess.run(["ruff", "format"] + [str(f) for f in files],
                      capture_output=True)

    def run_pytest(self) -> bool:
        """Run pytest with coverage"""
        result = subprocess.run([
            "python", "-m", "pytest", "tests/",
            "--cov=scripts", "--cov=tests",
            "--cov-report=term-missing",
            "--cov-report=html",
            "-v", "--strict-markers"
        ], capture_output=True, text=True)

        if result.returncode != 0:
            self.errors.append(("Tests", "One or more tests failed"))
            return False
        return True

    def check_coverage_threshold(self) -> bool:
        """Check coverage meets 80% threshold"""
        result = subprocess.run(["coverage", "report"],
                               capture_output=True, text=True)

        # Parse total coverage percentage
        for line in result.stdout.splitlines():
            if line.startswith("TOTAL"):
                coverage_pct = float(line.split()[3].rstrip("%"))

                if coverage_pct < 80:
                    self.errors.append(
                        ("Coverage", f"{coverage_pct}% < 80% threshold")
                    )
                    return False
                return True

        self.errors.append(("Coverage", "Could not parse coverage report"))
        return False

    def check_complexity(self, files: List[Path]) -> bool:
        """Check cyclomatic complexity with radon"""
        if not files:
            return True

        cmd = ["radon", "cc"] + [str(f) for f in files] + ["-n", "C"]
        result = subprocess.run(cmd, capture_output=True, text=True)

        # Look for functions with complexity > 15
        for line in result.stdout.splitlines():
            if line.strip() and "-" in line:
                # Extract complexity value (e.g., "scripts/generate_dataset.py:123:16: C")
                parts = line.split()
                if len(parts) >= 2:
                    # Extract complexity number
                    complexity_str = parts[-2] if parts[-2].isdigit() else parts[-1]
                    if complexity_str.isdigit():
                        complexity = int(complexity_str)
                        if complexity > 15:
                            self.errors.append(
                                ("Complexity", f"Function exceeds threshold: {line}")
                            )

        if self.errors and any(e[0] == "Complexity" for e in self.errors):
            return False
        return True

    def print_report(self):
        """Print color-coded report of results"""
        print("\n" + "="*60)
        print("QUALITY CHECK REPORT")
        print("="*60)

        if not self.errors:
            print("\033[92m✅ All checks passed!\033[0m")
            return

        print("\n\033[91m❌ The following issues were found:\033[0m\n")

        for check_type, message in self.errors:
            if check_type == "Linting":
                print(f"\033[91m{check_type}:\033[0m")
                print(message)
                print()
            elif check_type == "Tests":
                print(f"\033[91m{check_type}: {message}\033[0m\n")
            elif check_type == "Coverage":
                print(f"\033[91m{check_type}: {message}\033[0m\n")
            elif check_type == "Complexity":
                print(f"\033[91m{check_type}: {message}\033[0m")

        print("\nRun `python scripts/quality_check.py --fix` to auto-fix linting issues")
        print("Run `python scripts/quality_check.py --all` to check all files")

    def run(self) -> int:
        """Main workflow - runs all checks in sequence"""
        self.parse_args()

        # 1. Detect files to check
        files = self.get_files_to_check()
        if not files:
            print("No Python files to check.")
            return 0

        # 2. Linting (with optional auto-fix)
        if self.config.fix:
            print("\033[93m🔧 Auto-fixing linting issues...\033[0m")
            self.run_ruff_fix(files)

        lint_passed = self.run_ruff_check(files)

        # 3. Testing (always run full suite)
        print("\033[93m🧪 Running tests...\033[0m")
        test_passed = self.run_pytest()

        # 4. Coverage validation
        print("\033[93m📊 Checking coverage...\033[0m")
        coverage_passed = self.check_coverage_threshold()

        # 5. Complexity analysis
        print("\033[93m🧮 Checking code complexity...\033[0m")
        complexity_passed = self.check_complexity(files)

        # 6. Report results
        self.print_report()

        # 7. Return exit code (fail hard in strict mode)
        if not all([lint_passed, test_passed, coverage_passed, complexity_passed]):
            return 1
        return 0

def main():
    """Entry point for console script"""
    checker = QualityChecker()
    sys.exit(checker.run())

if __name__ == "__main__":
    main()
