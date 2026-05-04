#!/usr/bin/env python3
"""Combined triage + sync: filter new issues, then sync triaged ones to Kanban."""
import subprocess
import sys
import os

SCRIPTS_DIR = os.path.expanduser("~/heventure-search-mcp/scripts")

def run_script(name: str, dry_run: bool = False) -> str:
    cmd = ["python3", os.path.join(SCRIPTS_DIR, name)]
    if dry_run:
        cmd.append("--dry-run")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    return result.stdout + result.stderr

def main():
    dry_run = "--dry-run" in sys.argv
    
    print("=" * 60)
    print("🔍 Issue Triage + Sync Pipeline")
    print("=" * 60)

    # Step 1: Triage new issues
    print("\n📋 Step 1: Triage incoming issues...")
    print("-" * 40)
    triage_output = run_script("issue_triage.py", dry_run)
    print(triage_output)

    # Step 2: Sync triaged issues to Kanban
    print("\n🔄 Step 2: Sync triaged issues to Kanban...")
    print("-" * 40)
    sync_output = run_script("kanban_github_sync.py", dry_run)
    print(sync_output)

if __name__ == "__main__":
    main()
