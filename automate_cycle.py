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
ISSUE_TITLE = "Fix: Backend NameError (Missing Definitions)"
ISSUE_BODY = """
Restored `router_v1`, `ChatResponse`, and `detect_anomalies` which were accidentally overwritten in previous edits.
"""

COMMIT_MSG = "fix: restore missing backend definitions causing startup crash"

PR_TITLE = "Emergency: Fix Backend Startup"
PR_BODY = "Restores critical missing symbols."

print("🕵️‍♂️ Open-Detective High-Level Workflow Starting...")

# 1. 建立具有侦探深度的 Issue
issue_res = run(f'gh issue create --title "{ISSUE_TITLE}" --body "{ISSUE_BODY}"')
issue_url = issue_res.stdout.strip()

# 2. 切换分支并强制抓取所有修改
run('git checkout -B feature/detective-core-upgrade')
run('git add .')
run(f'git commit -m "{COMMIT_MSG}"')
run('git push -f origin feature/detective-core-upgrade')

# 3. 创建 PR 并完成闭环
run(f'gh pr create --title "{PR_TITLE}" --body "{PR_BODY}" --base main --head feature/detective-core-upgrade')
run('gh pr merge --merge --delete-branch')

# 4. 显式关闭 Issue
if issue_url:
    print(f"🔒 Closing Issue: {issue_url}")
    run(f'gh issue close {issue_url}')

print("✅ Investigation Cycle Successfully Merged and Documented!")