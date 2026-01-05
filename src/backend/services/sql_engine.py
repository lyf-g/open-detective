def mock_text_to_sql(text: str) -> str:
    """
    A very simple rule-based 'AI' for the MVP.
    Real implementation will use LLM here.
    """
    text = text.lower()
    
    # improved detection logic
    repo = None
    if "vue" in text: repo = "vuejs/core"
    elif "fastapi" in text: repo = "fastapi/fastapi"
    elif "react" in text: repo = "facebook/react"
    elif "tensorflow" in text: repo = "tensorflow/tensorflow"
    elif "vscode" in text: repo = "microsoft/vscode"
    elif "kubernetes" in text or "k8s" in text: repo = "kubernetes/kubernetes"
    
    metric = "stars" # default
    if "activity" in text: metric = "activity"
    elif "rank" in text: metric = "openrank"
    elif "bus" in text or "risk" in text: metric = "bus_factor"
    elif "closed" in text and "issue" in text: metric = "issues_closed"
    elif "issue" in text or "bug" in text: metric = "issues_new"
    
    if repo:
        return f"SELECT month, value FROM open_digger_metrics WHERE repo_name = '{repo}' AND metric_type = '{metric}' ORDER BY month ASC"
    
    return ""
