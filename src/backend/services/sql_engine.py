import json
import os

def mock_text_to_sql(text: str) -> str:
    """
    A rule-based 'AI' that dynamically matches against supported repositories.
    """
    text = text.lower()
    
    # Load supported repositories from config
    config_path = os.path.join(os.path.dirname(__file__), '../../../data/repos.json')
    try:
        with open(config_path, 'r') as f:
            repo_list = json.load(f)
    except Exception:
        repo_list = []

    # Dynamic repository matching
    repo = None
    text_words = text.replace('/', ' ').replace('-', ' ').replace('_', ' ').split()
    # Keywords to ignore when matching repositories
    ignore_keywords = ['stars', 'activity', 'rank', 'openrank', 'bus', 'factor', 'risk', 'issue', 'issues', 'bug', 'bugs', 'closed', 'for', 'the', 'and', 'with', 'show', 'me', 'what', 'is', 'lang', 'core', 'git']
    
    # 1. Try exact full name match first
    for r in repo_list:
        if r.lower() in text:
            repo = r
            break
            
    if not repo:
        for r in repo_list:
            full_name_lower = r.lower()
            segments = full_name_lower.replace('/', ' ').replace('-', ' ').replace('_', ' ').split()
            
            # 2. Try exact match of any unique segment
            if any(word in segments for word in text_words if word not in ignore_keywords):
                repo = r
                break
            
            # 3. Try substring match (e.g. 'vue' matches 'vuejs')
            if any(word in seg for seg in segments for word in text_words if word not in ignore_keywords and len(word) >= 3):
                repo = r
                break
    
    # Special aliases
    if not repo:
        if "k8s" in text: repo = "kubernetes/kubernetes"
    
    metric = "stars" # default
    if "activity" in text: metric = "activity"
    elif "rank" in text: metric = "openrank"
    elif "bus" in text or "risk" in text: metric = "bus_factor"
    elif "closed" in text and "issue" in text: metric = "issues_closed"
    elif "issue" in text or "bug" in text: metric = "issues_new"
    
    if repo:
        return f"SELECT month, value FROM open_digger_metrics WHERE repo_name = '{repo}' AND metric_type = '{metric}' ORDER BY month ASC"
    
    return ""
