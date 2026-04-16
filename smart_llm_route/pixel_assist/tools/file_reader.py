import os
from pathlib import Path
from typing import Any, Dict, List, Optional


class FileReader:
    def __init__(self, base_path: Optional[str] = None):
        self.base_path = Path(base_path) if base_path else Path.cwd()

    def _resolve_path(self, path: str) -> Path:
        p = Path(path)
        if not p.is_absolute():
            p = self.base_path / p
        return p.resolve()

    def read_file(self, path: str, encoding: str = "utf-8") -> Dict[str, Any]:
        try:
            file_path = self._resolve_path(path)
            
            if not file_path.exists():
                return {"success": False, "error": f"File not found: {path}"}
            
            if not file_path.is_file():
                return {"success": False, "error": f"Not a file: {path}"}
            
            content = file_path.read_text(encoding=encoding)
            
            lines = content.split("\n")
            line_count = len(lines)
            
            return {
                "success": True,
                "path": str(file_path),
                "content": content,
                "line_count": line_count,
                "size": file_path.stat().st_size
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def read_multiple(self, paths: List[str], encoding: str = "utf-8") -> Dict[str, Any]:
        results = {}
        for path in paths:
            results[path] = self.read_file(path, encoding)
        return results

    def list_directory(self, path: str = ".", pattern: Optional[str] = None) -> Dict[str, Any]:
        try:
            dir_path = self._resolve_path(path)
            
            if not dir_path.exists():
                return {"success": False, "error": f"Directory not found: {path}"}
            
            if not dir_path.is_dir():
                return {"success": False, "error": f"Not a directory: {path}"}
            
            items = []
            for item in dir_path.iterdir():
                items.append({
                    "name": item.name,
                    "type": "directory" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else 0
                })
            
            if pattern:
                items = [i for i in items if pattern in i["name"]]
            
            return {
                "success": True,
                "path": str(dir_path),
                "items": sorted(items, key=lambda x: (x["type"], x["name"]))
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def search_in_file(self, path: str, pattern: str, case_sensitive: bool = False) -> Dict[str, Any]:
        try:
            file_result = self.read_file(path)
            if not file_result["success"]:
                return file_result
            
            content = file_result["content"]
            if not case_sensitive:
                content = content.lower()
                pattern = pattern.lower()
            
            lines = content.split("\n")
            matches = []
            
            for i, line in enumerate(lines, 1):
                if pattern in line:
                    matches.append({
                        "line_number": i,
                        "content": line.strip()
                    })
            
            return {
                "success": True,
                "path": path,
                "pattern": pattern,
                "match_count": len(matches),
                "matches": matches
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_file_info(self, path: str) -> Dict[str, Any]:
        try:
            file_path = self._resolve_path(path)
            
            if not file_path.exists():
                return {"success": False, "error": f"File not found: {path}"}
            
            stat = file_path.stat()
            
            return {
                "success": True,
                "path": str(file_path),
                "name": file_path.name,
                "size": stat.st_size,
                "is_file": file_path.is_file(),
                "is_directory": file_path.is_dir(),
                "modified": stat.st_mtime,
                "created": stat.st_ctime
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
