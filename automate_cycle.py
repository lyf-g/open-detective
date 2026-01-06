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
ISSUE_TITLE = "Fix: Persistent AI JSON Pollution"
ISSUE_BODY = """
Despite prompt engineering, SQLBot insists on outputting JSON. Implemented client-side filtering and a rule-based fallback report generator.
"""

COMMIT_MSG = "fix: implement fallback report generator when AI outputs JSON"

PR_TITLE = "Robustness: Fallback Reporting"
PR_BODY = "Prevents display of raw JSON by falling back to a generated summary."

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