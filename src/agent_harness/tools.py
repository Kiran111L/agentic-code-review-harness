from pathlib import Path
from typing import Any
from .safety import safe_path, EXCLUDED_DIRS

class ToolError(Exception):
    pass

class ToolRegistry:
    def __init__(self, root: str, max_file_bytes: int = 200_000):
        self.root = Path(root).resolve()
        if not self.root.is_dir():
            raise ValueError(f"Project path is not a directory: {root}")
        self.max_file_bytes = max_file_bytes
        self.permissions = {
            "planner": {"list_files", "project_summary"},
            "bug": {"list_files", "read_file", "get_line_range"},
            "security": {"list_files", "read_file", "get_line_range", "search_text"},
            "quality": {"list_files", "read_file", "get_line_range", "project_summary"},
            "checker": {"get_line_range", "validate_finding"},
            "baseline": {"list_files", "read_file", "get_line_range", "search_text", "project_summary"},
        }

    def call(self, role: str, name: str, args: dict[str, Any]) -> Any:
        if name not in self.permissions.get(role, set()):
            raise ToolError(f"Tool '{name}' is not permitted for role '{role}'")
        method = getattr(self, f"_{name}", None)
        if method is None:
            raise ToolError(f"Unknown tool: {name}")
        return method(**args)

    def _iter_files(self):
        for path in sorted(self.root.rglob("*")):
            if any(part in EXCLUDED_DIRS for part in path.parts):
                continue
            if path.is_file() and path.suffix.lower() in {".py", ".md", ".toml", ".ini", ".cfg", ".txt", ".yaml", ".yml", ".json"}:
                try:
                    safe_path(self.root, path.relative_to(self.root).as_posix())
                except ValueError:
                    continue
                if path.stat().st_size <= self.max_file_bytes:
                    yield path

    def _list_files(self, limit: int = 100):
        return [p.relative_to(self.root).as_posix() for p in list(self._iter_files())[:max(1, min(limit, 500))]]

    def _read_file(self, path: str):
        target = safe_path(self.root, path)
        if not target.is_file():
            raise ToolError("File does not exist")
        if target.stat().st_size > self.max_file_bytes:
            raise ToolError("File exceeds size limit")
        return target.read_text(encoding="utf-8", errors="replace")

    def _get_line_range(self, path: str, start_line: int, end_line: int):
        if start_line < 1 or end_line < start_line or end_line - start_line > 100:
            raise ToolError("Invalid line range")
        lines = self._read_file(path).splitlines()
        if start_line > len(lines):
            raise ToolError("Start line is outside file")
        return "\n".join(f"{i}: {lines[i-1]}" for i in range(start_line, min(end_line, len(lines))+1))

    def _search_text(self, query: str, limit: int = 30):
        results = []
        for path in self._iter_files():
            try:
                for i, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                    if query.lower() in line.lower():
                        results.append({"file": path.relative_to(self.root).as_posix(), "line": i, "text": line[:500]})
                        if len(results) >= min(max(1, limit), 100):
                            return results
            except OSError:
                continue
        return results

    def _project_summary(self):
        paths = list(self._iter_files())
        return {"file_count": len(paths), "line_count": sum(len(p.read_text(encoding="utf-8", errors="replace").splitlines()) for p in paths)}

    def _validate_finding(self, finding: dict):
        try:
            path = safe_path(self.root, finding["file_path"])
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
            start, end = finding["start_line"], finding["end_line"]
            if start < 1 or end < start or end > len(lines):
                return {"valid": False, "reason": "Line range is outside source"}
            evidence = finding["evidence"].strip()
            source = "\n".join(lines[start-1:end])
            normalized = lambda s: " ".join(s.split())
            if not evidence or normalized(evidence) not in normalized(source):
                return {"valid": False, "reason": "Evidence does not match referenced source lines"}
            return {"valid": True, "reason": "Evidence text and line range match"}
        except (ValueError, OSError, KeyError, TypeError) as exc:
            return {"valid": False, "reason": str(exc)}
