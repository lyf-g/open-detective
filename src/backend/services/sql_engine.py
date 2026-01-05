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
    for r in repo_list:
        # Match if the short name (e.g. 'ollama') or full name is in the text
        short_name = r.split('/')[-1].lower()
        if short_name in text or r.lower() in text:
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
