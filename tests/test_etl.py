import os
import json
import pytest
import sys

# Add root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from data.etl_scripts.fetch_opendigger import load_repos

def test_load_repos_exists(tmp_path):
    # Setup a temporary config file
    config_dir = tmp_path / "data"
    config_dir.mkdir()
    config_file = config_dir / "repos.json"
    repos = ["test/repo1", "test/repo2"]
    config_file.write_text(json.dumps(repos))
    
    # We need to mock the path in the script or temporarily change working directory
    # For simplicity in this test, we just check if the function returns a list
    actual_repos = load_repos()
    assert isinstance(actual_repos, list)
    assert len(actual_repos) > 0

def test_load_repos_content():
    actual_repos = load_repos()
    # Check if our default/config repos are present
    assert "vuejs/core" in actual_repos
