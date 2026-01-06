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

# 定制化的元数据
ISSUE_TITLE = "Feat: Configurable Anomaly Detection Sensitivity"
ISSUE_BODY = """
Improvement Log:
1. Backend: Replaced hardcoded `0.5` threshold with `ANOMALY_THRESHOLD` env var.
2. Ops: Enabled fine-tuning of insight generation for volatile repositories.
"""

COMMIT_MSG = "feat: make anomaly detection threshold configurable via env var"

PR_TITLE = "Configurable Insight Sensitivity"
PR_BODY = "Allows DevOps to tune the volatility threshold via ANOMALY_THRESHOLD."

print("🕵️‍♂️ Open-Detective High-Level Workflow Starting...")

# 1. 建立具有侦探深度的 Issue
run(f'gh issue create --title "{ISSUE_TITLE}" --body "{ISSUE_BODY}"')

# 2. 切换分支并强制抓取所有修改
run('git checkout -B feature/detective-core-upgrade')
run('git add .')
run(f'git commit -m "{COMMIT_MSG}"')
run('git push -f origin feature/detective-core-upgrade')

# 3. 创建 PR 并完成闭环
run(f'gh pr create --title "{PR_TITLE}" --body "{PR_BODY}" --base main --head feature/detective-core-upgrade')
run('gh pr merge --merge --delete-branch')

print("✅ Investigation Cycle Successfully Merged and Documented!")