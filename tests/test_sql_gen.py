import sys
import os
import pytest

# Add src to python path so we can import modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from src.backend.services.sql_engine import mock_text_to_sql

def test_sql_gen_basic():
    sql = mock_text_to_sql("stars for vue")
    assert "repo_name = 'vuejs/core'" in sql
    assert "metric_type = 'stars'" in sql

def test_sql_gen_activity():
    sql = mock_text_to_sql("activity of react")
    assert "repo_name = 'facebook/react'" in sql
    assert "metric_type = 'activity'" in sql

def test_sql_gen_bus_factor():
    sql = mock_text_to_sql("what is the bus factor of tensorflow")
    assert "repo_name = 'tensorflow/tensorflow'" in sql
    assert "metric_type = 'bus_factor'" in sql

def test_sql_gen_unknown_repo():
    sql = mock_text_to_sql("stars for unknown_repo")
    assert sql == ""

def test_sql_gen_vscode():
    sql = mock_text_to_sql("vscode issues")
    assert "repo_name = 'microsoft/vscode'" in sql
    assert "metric_type = 'issues_new'" in sql

def test_sql_gen_ollama():
    sql = mock_text_to_sql("stars for ollama")
    assert "repo_name = 'ollama/ollama'" in sql

def test_sql_gen_rust():
    sql = mock_text_to_sql("activity of rust-lang/rust")
    assert "repo_name = 'rust-lang/rust'" in sql

