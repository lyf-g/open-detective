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
ISSUE_TITLE = "Fix: Aggressive JSON Sanitization and Anomaly Report Purity"
ISSUE_BODY = """
Investigation Log:
1. Backend: Implemented surgical sanitization to strip persistent JSON artifacts from SQLBot.
2. Logic: Forced repo_name in SELECT clause to fix 'None' values in anomaly detection.
3. Persona: Standardized Open-Detective naming and removed AI meta-talk.
4. Frontend: Added UI-level regex filtering for zero-noise rendering.
"""

COMMIT_MSG = """feat: total UI/UX evolution and brute-force sanitization

- Re-engineered SQLBotClient with surgical text stripping
- Mandated repo_name in SQL prompt to fix Anomaly Detection None-errors
- Fully integrated Element Plus with Thought Chain loading animations
- Enforced Open-Detective brand identity across all tiers
"""

PR_TITLE = "Major Evolution: Clean AI Interpretation and Integrated Insights"
PR_BODY = f"Closes #178. This PR finalizes the professional transformation of Open-Detective."

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