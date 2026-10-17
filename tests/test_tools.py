from pathlib import Path
import pytest
from agent_harness.tools import ToolRegistry, ToolError

def test_path_traversal_and_credentials_blocked(tmp_path):
    root = tmp_path / "project"; root.mkdir()
    (root / "app.py").write_text("print('ok')\n")
    (root / ".env").write_text("API_KEY=secret")
    outside = tmp_path / "outside.py"; outside.write_text("x=1")
    t = ToolRegistry(str(root))
    with pytest.raises(ValueError):
        t.call("bug", "read_file", {"path":"../outside.py"})
    with pytest.raises(ValueError):
        t.call("bug", "read_file", {"path":".env"})
    with pytest.raises(ToolError):
        t.call("bug", "search_text", {"query":"x"})
    assert "app.py" in t.call("bug", "list_files", {})

def test_symlink_outside_root_is_rejected(tmp_path):
    root = tmp_path / "project"; root.mkdir()
    outside = tmp_path / "outside.py"; outside.write_text("secret = 1\n")
    (root / "link.py").symlink_to(outside)
    tools = ToolRegistry(str(root))
    assert "link.py" not in tools.call("bug", "list_files", {})
