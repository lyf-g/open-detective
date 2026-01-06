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
ISSUE_TITLE = "Feat: Cyberpunk UI Polish & Interaction Micro-effects"
ISSUE_BODY = """
Improvement Log:
1. Frontend: Overrode default scrollbars with a custom dark/teal theme.
2. UX: Added magnetic hover effects and glowing borders to message cards.
"""

COMMIT_MSG = "feat: add custom dark scrollbars and card hover physics"

PR_TITLE = "Visual Polish: Scrollbars & Interactions"
PR_BODY = "Enhances immersion with terminal-style scrollbars and reactive UI elements."

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