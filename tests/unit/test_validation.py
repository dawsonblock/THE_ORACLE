import subprocess
import sys
from integration.validation import run_tests

def test_run_tests_returns_tuple(tmp_path):
    """Test that run_tests returns the expected tuple structure."""
    repo = tmp_path / "repo"
    repo.mkdir()
    
    # Create a simple Python file
    (repo / "test_dummy.py").write_text("def test_dummy(): assert True\n", encoding="utf-8")
    
    ok, output, meta = run_tests(str(repo))
    
    assert isinstance(ok, bool)
    assert isinstance(output, str)
    assert isinstance(meta, dict)
    assert "syntax_ok" in meta
    assert "test_command" in meta
