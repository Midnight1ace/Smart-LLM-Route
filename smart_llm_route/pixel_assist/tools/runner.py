import json
import re
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass

from .file_reader import FileReader
from .file_editor import FileEditor
from .executor import Executor


@dataclass
class ToolResult:
    tool: str
    success: bool
    result: Dict[str, Any]
    error: Optional[str] = None


class ToolRunner:
    def __init__(
        self,
        base_path: Optional[str] = None,
        allow_execution: bool = True
    ):
        self.base_path = base_path
        self.allow_execution = allow_execution
        
        self.file_reader = FileReader(base_path)
        self.file_editor = FileEditor(base_path)
        self.executor = Executor(base_path) if allow_execution else None
        
        self._tool_registry: Dict[str, Callable] = {
            "read_file": self._read_file,
            "read_multiple": self._read_multiple,
            "list_directory": self._list_directory,
            "search_in_file": self._search_in_file,
            "get_file_info": self._get_file_info,
            "edit_file": self._edit_file,
            "create_file": self._create_file,
            "append_to_file": self._append_to_file,
            "delete_file": self._delete_file,
            "delete_directory": self._delete_directory,
            "move_file": self._move_file,
            "copy_file": self._copy_file,
            "create_directory": self._create_directory,
            "execute": self._execute,
            "execute_python": self._execute_python,
            "run_python_script": self._run_python_script,
        }

    def _read_file(self, path: str, **kwargs) -> Dict[str, Any]:
        return self.file_reader.read_file(path)

    def _read_multiple(self, paths: List[str], **kwargs) -> Dict[str, Any]:
        return self.file_reader.read_multiple(paths)

    def _list_directory(self, path: str = ".", pattern: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        return self.file_reader.list_directory(path, pattern)

    def _search_in_file(self, path: str, pattern: str, case_sensitive: bool = False, **kwargs) -> Dict[str, Any]:
        return self.file_reader.search_in_file(path, pattern, case_sensitive)

    def _get_file_info(self, path: str, **kwargs) -> Dict[str, Any]:
        return self.file_reader.get_file_info(path)

    def _edit_file(self, path: str, old: str, new: str, replace_all: bool = False, **kwargs) -> Dict[str, Any]:
        return self.file_editor.edit_file(path, old, new, replace_all)

    def _create_file(self, path: str, content: str = "", **kwargs) -> Dict[str, Any]:
        return self.file_editor.create_file(path, content)

    def _append_to_file(self, path: str, content: str, **kwargs) -> Dict[str, Any]:
        return self.file_editor.append_to_file(path, content)

    def _delete_file(self, path: str, **kwargs) -> Dict[str, Any]:
        return self.file_editor.delete_file(path)

    def _delete_directory(self, path: str, **kwargs) -> Dict[str, Any]:
        return self.file_editor.delete_directory(path)

    def _move_file(self, src: str, dest: str, **kwargs) -> Dict[str, Any]:
        return self.file_editor.move_file(src, dest)

    def _copy_file(self, src: str, dest: str, **kwargs) -> Dict[str, Any]:
        return self.file_editor.copy_file(src, dest)

    def _create_directory(self, path: str, **kwargs) -> Dict[str, Any]:
        return self.file_editor.create_directory(path)

    def _execute(self, command: str, timeout: Optional[int] = None, **kwargs) -> Dict[str, Any]:
        if not self.allow_execution:
            return {"success": False, "error": "Execution disabled"}
        return self.executor.execute(command, timeout)

    def _execute_python(self, code: str, timeout: Optional[int] = None, **kwargs) -> Dict[str, Any]:
        if not self.allow_execution:
            return {"success": False, "error": "Execution disabled"}
        return self.executor.execute_python(code, timeout)

    def _run_python_script(self, script_path: str, args: Optional[List[str]] = None, **kwargs) -> Dict[str, Any]:
        if not self.allow_execution:
            return {"success": False, "error": "Execution disabled"}
        return self.executor.run_python_script(script_path, args)

    def run_tool(self, tool_name: str, **kwargs) -> ToolResult:
        if tool_name not in self._tool_registry:
            return ToolResult(
                tool=tool_name,
                success=False,
                result={},
                error=f"Unknown tool: {tool_name}"
            )
        
        try:
            result = self._tool_registry[tool_name](**kwargs)
            return ToolResult(
                tool=tool_name,
                success=result.get("success", True),
                result=result,
                error=result.get("error")
            )
        except Exception as e:
            return ToolResult(
                tool=tool_name,
                success=False,
                result={},
                error=str(e)
            )

    def list_tools(self) -> List[str]:
        return list(self._tool_registry.keys())

    def parse_tool_calls(self, response: str) -> List[Dict[str, Any]]:
        tool_calls = []
        
        json_pattern = r'```json\s*([\s\S]*?)\s*```'
        matches = re.findall(json_pattern, response)
        
        for match in matches:
            try:
                tool_call = json.loads(match)
                if isinstance(tool_call, dict) and "tool" in tool_call:
                    tool_calls.append(tool_call)
                elif isinstance(tool_call, list):
                    tool_calls.extend([t for t in tool_call if isinstance(t, dict) and "tool" in t])
            except json.JSONDecodeError:
                continue
        
        return tool_calls

    def execute_tool_calls(self, tool_calls: List[Dict[str, Any]]) -> List[ToolResult]:
        results = []
        for tool_call in tool_calls:
            tool_name = tool_call.get("tool")
            args = tool_call.get("args", {})
            
            result = self.run_tool(tool_name, **args)
            results.append(result)
        
        return results
