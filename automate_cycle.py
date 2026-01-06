import subprocess
import os

def run(cmd):
    print(f"Executing: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
    else:
        print(result.stdout)
    return result

print("🕵️‍♂️ Open-Detective Automated Workflow Starting...")

# 1. Create GH Issue
run('gh issue create --title "Feature: Extreme UI and AI Sanitization" --body "Integrated anomaly detection and brute-force JSON stripping."')

# 2. Git Cycle
run('git checkout -b feature/final-evolution')
run('git add .')
run('git commit -m "feat: complete professional evolution - UI, Sanitization, and Anomaly Detection"')
run('git push origin feature/final-evolution')

# 3. Pull Request & Merge
run('gh pr create --title "Final Professional Evolution" --body "Complete UI/UX and backend stability overhaul."')
run('gh pr merge --merge --delete-branch')

print("✅ Automation Cycle Complete!")
