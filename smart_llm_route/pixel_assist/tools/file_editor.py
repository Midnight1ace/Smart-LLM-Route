import os
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional


class FileEditor:
    def __init__(self, base_path: Optional[str] = None):
        self.base_path = Path(base_path) if base_path else Path.cwd()
        self._backup_enabled = True
        self._backup_dir = self.base_path / ".pixel_assist_backups"

    def _resolve_path(self, path: str) -> Path:
        p = Path(path)
        if not p.is_absolute():
            p = self.base_path / p
        return p.resolve()

    def _create_backup(self, file_path: Path) -> Optional[Path]:
        if not self._backup_enabled:
            return None
        
        self._backup_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = Path(file_path).name + f"_{int(os.times().elapsed * 1000)}"
        backup_path = self._backup_dir / timestamp
        
        shutil.copy2(file_path, backup_path)
        return backup_path

    def edit_file(
        self,
        path: str,
        old: str,
        new: str,
        replace_all: bool = False
    ) -> Dict[str, Any]:
        try:
            file_path = self._resolve_path(path)
            
            if not file_path.exists():
                return {"success": False, "error": f"File not found: {path}"}
            
            if not file_path.is_file():
                return {"success": False, "error": f"Not a file: {path}"}
            
            content = file_path.read_text(encoding="utf-8")
            
            if old not in content:
                return {"success": False, "error": "Pattern not found in file"}
            
            self._create_backup(file_path)
            
            if replace_all:
                new_content = content.replace(old, new)
            else:
                new_content = content.replace(old, new, 1)
            
            file_path.write_text(new_content, encoding="utf-8")
            
            return {
                "success": True,
                "path": str(file_path),
                "replaced": not replace_all,
                "all": replace_all
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def create_file(self, path: str, content: str = "", encoding: str = "utf-8") -> Dict[str, Any]:
        try:
            file_path = self._resolve_path(path)
            
            if file_path.exists():
                return {"success": False, "error": f"File already exists: {path}"}
            
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding=encoding)
            
            return {
                "success": True,
                "path": str(file_path),
                "size": len(content)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def append_to_file(self, path: str, content: str, encoding: str = "utf-8") -> Dict[str, Any]:
        try:
            file_path = self._resolve_path(path)
            
            if not file_path.exists():
                return {"success": False, "error": f"File not found: {path}"}
            
            with open(file_path, "a", encoding=encoding) as f:
                f.write(content)
            
            return {
                "success": True,
                "path": str(file_path),
                "bytes_written": len(content)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def delete_file(self, path: str) -> Dict[str, Any]:
        try:
            file_path = self._resolve_path(path)
            
            if not file_path.exists():
                return {"success": False, "error": f"File not found: {path}"}
            
            if not file_path.is_file():
                return {"success": False, "error": f"Not a file: {path}"}
            
            self._create_backup(file_path)
            file_path.unlink()
            
            return {
                "success": True,
                "path": str(file_path)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def delete_directory(self, path: str) -> Dict[str, Any]:
        try:
            dir_path = self._resolve_path(path)
            
            if not dir_path.exists():
                return {"success": False, "error": f"Directory not found: {path}"}
            
            if not dir_path.is_dir():
                return {"success": False, "error": f"Not a directory: {path}"}
            
            shutil.rmtree(dir_path)
            
            return {
                "success": True,
                "path": str(dir_path)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def move_file(self, src: str, dest: str) -> Dict[str, Any]:
        try:
            src_path = self._resolve_path(src)
            dest_path = self._resolve_path(dest)
            
            if not src_path.exists():
                return {"success": False, "error": f"Source not found: {src}"}
            
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src_path), str(dest_path))
            
            return {
                "success": True,
                "from": str(src_path),
                "to": str(dest_path)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def copy_file(self, src: str, dest: str) -> Dict[str, Any]:
        try:
            src_path = self._resolve_path(src)
            dest_path = self._resolve_path(dest)
            
            if not src_path.exists():
                return {"success": False, "error": f"Source not found: {src}"}
            
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_path, dest_path)
            
            return {
                "success": True,
                "from": str(src_path),
                "to": str(dest_path)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def create_directory(self, path: str) -> Dict[str, Any]:
        try:
            dir_path = self._resolve_path(path)
            
            if dir_path.exists():
                return {"success": False, "error": f"Directory already exists: {path}"}
            
            dir_path.mkdir(parents=True, exist_ok=True)
            
            return {
                "success": True,
                "path": str(dir_path)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def write_lines(self, path: str, lines: List[str]) -> Dict[str, Any]:
        try:
            content = "\n".join(lines)
            return self.create_file(path, content)
        except Exception as e:
            return {"success": False, "error": str(e)}
