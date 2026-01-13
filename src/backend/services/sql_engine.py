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
    found_repos = set()
    # Clean text: remove common punctuation and split
    cleaned_text = text.replace('/', ' ').replace('-', ' ').replace('_', ' ').replace(',', ' ').replace('.', ' ').replace('?', ' ').replace('!', ' ').replace('，', ' ').replace('？', ' ').replace('！', ' ').replace('。', ' ')
    text_words = cleaned_text.split()
    
    # Keywords to ignore when matching repositories
    ignore_keywords = ['stars', 'activity', 'rank', 'openrank', 'bus', 'factor', 'risk', 'issue', 'issues', 'bug', 'bugs', 'closed', 'for', 'the', 'and', 'with', 'show', 'me', 'what', 'is', 'lang', 'core', 'git', 'compare', 'vs', 'versus', 'of']
    
    # Check for K8s alias explicitly
    if "k8s" in text:
        found_repos.add("kubernetes/kubernetes")

    for r in repo_list:
        full_name_lower = r.lower()
        
        # 1. Try exact full name match
        if full_name_lower in text:
            found_repos.add(r)
            continue

        segments = full_name_lower.replace('/', ' ').replace('-', ' ').replace('_', ' ').split()
        
        # 2. Try exact match of any unique segment OR substring match (starts with)
        is_match = False
        for word in text_words:
            if word in ignore_keywords: continue
            
            # Exact segment match
            if word in segments:
                is_match = True
                break
            
            # Substring match (e.g. 'vue' matches 'vuejs') - Enforce startswith to avoid 'react' matching 'preact'
            if len(word) >= 3 and any(seg.startswith(word) for seg in segments):
                is_match = True
                break
        
        if is_match:
            found_repos.add(r)
    
    metric = "stars" # default
    if "activity" in text: metric = "activity"
    elif "rank" in text: metric = "openrank"
    elif "bus" in text or "risk" in text: metric = "bus_factor"
    elif "closed" in text and "issue" in text: metric = "issues_closed"
    elif "issue" in text or "bug" in text: metric = "issues_new"
    
    if found_repos:
        repo_list_str = "', '".join(found_repos)
        # Include repo_name in selection for frontend distinction
        return f"SELECT month, value, repo_name FROM open_digger_metrics WHERE repo_name IN ('{repo_list_str}') AND metric_type = '{metric}' ORDER BY month ASC"
    
    return ""
