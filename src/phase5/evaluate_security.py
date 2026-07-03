"""
Security & Credential Scan
============================
Scans the codebase for hardcoded API keys, tokens, passwords, and
other credential exposures.

Target: Zero credential exposures in source code.

Usage:
    python src/phase5/evaluate_security.py
"""

import os
import re
import sys
import json
from datetime import datetime

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# File extensions to scan
SCAN_EXTENSIONS = {".py", ".js", ".ts", ".jsx", ".tsx", ".json", ".yml", ".yaml", ".toml", ".cfg", ".ini", ".html", ".md"}

# Directories to skip
SKIP_DIRS = {"__pycache__", "node_modules", ".git", ".venv", "venv", "env", ".eggs", "chroma_db", ".system_generated"}

# Patterns that indicate hardcoded credentials
CREDENTIAL_PATTERNS = [
    (r"(?:api[_-]?key|apikey)\s*[=:]\s*['\"][a-zA-Z0-9_\-]{20,}['\"]", "Hardcoded API key"),
    (r"(?:secret|password|passwd|pwd)\s*[=:]\s*['\"][^'\"]{8,}['\"]", "Hardcoded secret/password"),
    (r"(?:token)\s*[=:]\s*['\"][a-zA-Z0-9_\-\.]{20,}['\"]", "Hardcoded token"),
    (r"sk-[a-zA-Z0-9]{20,}", "OpenAI API key pattern"),
    (r"gsk_[a-zA-Z0-9]{20,}", "Groq API key pattern"),
    (r"ghp_[a-zA-Z0-9]{36}", "GitHub personal access token"),
    (r"Bearer\s+[a-zA-Z0-9_\-\.]{20,}", "Hardcoded Bearer token"),
    (r"(?:AWS|aws)_(?:ACCESS|SECRET)[_A-Z]*\s*[=:]\s*['\"][A-Za-z0-9/+=]{16,}['\"]", "AWS credential"),
]

# Files that are EXPECTED to have credential patterns (false positives)
ALLOWED_FILES = {
    ".env",              # Environment file (not committed to git)
    ".env.example",      # Example env file
    "evaluate_security.py",  # This file itself contains patterns
}

# Patterns to check that .env is properly gitignored
GITIGNORE_REQUIRED = [".env", "*.db", "accounts.db"]


def scan_file(filepath: str) -> list[dict]:
    """Scan a single file for credential patterns."""
    findings = []
    basename = os.path.basename(filepath)

    if basename in ALLOWED_FILES:
        return []

    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
    except Exception:
        return []

    for line_num, line in enumerate(lines, 1):
        # Skip comments
        stripped = line.strip()
        if stripped.startswith("#") or stripped.startswith("//"):
            continue

        # Skip lines with "your_" placeholder values
        if "your_" in line.lower() and ("_here" in line.lower() or "placeholder" in line.lower()):
            continue

        for pattern, desc in CREDENTIAL_PATTERNS:
            matches = re.findall(pattern, line, re.IGNORECASE)
            if matches:
                # Filter out obvious placeholder/mock values
                for match in matches:
                    if any(p in match.lower() for p in ["your_", "placeholder", "example", "mock_", "test_"]):
                        continue
                    findings.append({
                        "file": os.path.relpath(filepath, PROJECT_ROOT),
                        "line": line_num,
                        "type": desc,
                        "snippet": stripped[:100] + ("..." if len(stripped) > 100 else ""),
                    })

    return findings


def check_gitignore() -> list[dict]:
    """Verify .gitignore contains required entries."""
    findings = []
    gitignore_path = os.path.join(PROJECT_ROOT, ".gitignore")

    if not os.path.exists(gitignore_path):
        findings.append({
            "type": "Missing .gitignore",
            "detail": "No .gitignore file found in project root",
            "severity": "HIGH",
        })
        return findings

    with open(gitignore_path, "r", encoding="utf-8") as f:
        content = f.read()

    for required in GITIGNORE_REQUIRED:
        if required not in content:
            findings.append({
                "type": f"Missing gitignore entry: {required}",
                "detail": f"'{required}' should be in .gitignore to prevent credential leaks",
                "severity": "HIGH",
            })

    return findings


def check_frontend_safety() -> list[dict]:
    """Ensure no API keys are referenced in frontend-facing code."""
    findings = []
    frontend_dirs = [
        os.path.join(PROJECT_ROOT, "src", "phase4"),
    ]

    sensitive_env_vars = ["GROQ_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY",
                          "SPOTIFY_CLIENT_SECRET", "REDDIT_CLIENT_SECRET"]

    for dir_path in frontend_dirs:
        if not os.path.exists(dir_path):
            continue
        for root, dirs, files in os.walk(dir_path):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for fname in files:
                if fname == "app.py":  # Streamlit app
                    filepath = os.path.join(root, fname)
                    try:
                        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()
                        for var in sensitive_env_vars:
                            if var in content and "os.getenv" not in content.split(var)[0].split("\n")[-1]:
                                findings.append({
                                    "file": os.path.relpath(filepath, PROJECT_ROOT),
                                    "type": f"Sensitive env var '{var}' referenced in frontend",
                                    "severity": "MEDIUM",
                                })
                    except Exception:
                        pass

    return findings


def run_evaluation():
    """Run the full security evaluation."""
    print("=" * 70)
    print("SECURITY & CREDENTIAL SCAN")
    print("=" * 70)
    print(f"Scanning: {PROJECT_ROOT}\n")

    # 1. Scan all source files
    all_findings = []
    files_scanned = 0

    for root, dirs, files in os.walk(PROJECT_ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for fname in files:
            ext = os.path.splitext(fname)[1].lower()
            if ext in SCAN_EXTENSIONS:
                filepath = os.path.join(root, fname)
                findings = scan_file(filepath)
                all_findings.extend(findings)
                files_scanned += 1

    print(f"Files scanned: {files_scanned}")

    # 2. Check .gitignore
    gitignore_findings = check_gitignore()

    # 3. Check frontend safety
    frontend_findings = check_frontend_safety()

    # ── Report ───────────────────────────────────────────────────────────
    print(f"\n--- Credential Scan ---")
    if all_findings:
        print(f"  FOUND {len(all_findings)} potential credential exposures:")
        for f in all_findings:
            print(f"    [{f['type']}] {f['file']}:{f['line']}")
            print(f"      {f['snippet']}")
    else:
        print(f"  No hardcoded credentials found")

    print(f"\n--- .gitignore Check ---")
    if gitignore_findings:
        for f in gitignore_findings:
            print(f"  [{f['severity']}] {f['type']}: {f['detail']}")
    else:
        print(f"  All required entries present")

    print(f"\n--- Frontend Safety ---")
    if frontend_findings:
        for f in frontend_findings:
            print(f"  [{f['severity']}] {f['type']}")
    else:
        print(f"  No sensitive credentials in frontend code")

    total_issues = len(all_findings) + len(gitignore_findings) + len(frontend_findings)
    high_severity = len([f for f in all_findings]) + len([f for f in gitignore_findings if f.get("severity") == "HIGH"])

    print(f"\n{'=' * 70}")
    print(f"RESULTS:")
    print(f"  Files scanned: {files_scanned}")
    print(f"  Total issues: {total_issues}")
    print(f"  High severity: {high_severity}")
    print(f"  Target: Zero credential exposures")
    overall_pass = high_severity == 0
    print(f"  Status: {'PASS' if overall_pass else 'FAIL'}")
    print(f"{'=' * 70}")

    # Save report
    report_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "workspace"))
    os.makedirs(report_dir, exist_ok=True)
    report_path = os.path.join(report_dir, "eval_security.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump({
            "test_date": datetime.now().isoformat(),
            "files_scanned": files_scanned,
            "credential_findings": all_findings,
            "gitignore_findings": [{"type": f["type"], "severity": f.get("severity", "")} for f in gitignore_findings],
            "frontend_findings": [{"type": f["type"], "severity": f.get("severity", "")} for f in frontend_findings],
            "total_issues": total_issues,
            "high_severity": high_severity,
            "overall_pass": overall_pass,
        }, f, indent=2)
    print(f"\nReport saved: {report_path}")

    return overall_pass


if __name__ == "__main__":
    success = run_evaluation()
    sys.exit(0 if success else 1)
