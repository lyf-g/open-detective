import sys
import os
import pytest

# Add src to python path so we can import modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from src.backend.services.sql_engine import mock_text_to_sql

def test_sql_gen_compare_vue_react():
    sql = mock_text_to_sql("compare vue and react stars")
    assert "repo_name IN" in sql
    assert "'vuejs/core'" in sql
    assert "'facebook/react'" in sql
    assert "metric_type = 'stars'" in sql
    assert "SELECT month, value, repo_name" in sql

def test_sql_gen_compare_three_repos():
    sql = mock_text_to_sql("activity of vue, react and tensorflow")
    assert "repo_name IN" in sql
    assert "'vuejs/core'" in sql
    assert "'facebook/react'" in sql
    assert "'tensorflow/tensorflow'" in sql
    assert "metric_type = 'activity'" in sql

def test_sql_gen_vs_keyword():
    sql = mock_text_to_sql("vue vs react")
    assert "repo_name IN" in sql
    assert "'vuejs/core'" in sql
    assert "'facebook/react'" in sql

def test_sql_gen_react_not_preact():
    sql = mock_text_to_sql("stars for react")
    assert "'facebook/react'" in sql
    # 'preactjs/preact' should NOT be in the result if strict matching works
    # "react" is not start of "preactjs" or "preact"
    assert "'preactjs/preact'" not in sql
