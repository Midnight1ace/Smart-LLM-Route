import os
import re
import subprocess
import shlex
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class Executor:
    DANGEROUS_PATTERNS = [
        r"rm\s+-rf",
        r"rm\s+/\s",
        r"format\s+",
        r"del\s+/[fqs]",
        r"mkfs",
        r"dd\s+if=",
        r">\s*/dev/",
        r"chmod\s+777",
        r"chown\s+-R",
        r"curl\s+.*\|\s*sh",
        r"wget\s+.*\|\s*sh",
        r":(){ :\|:& };:",
    ]

    def __init__(self, base_path: Optional[str] = None, allowed_commands: Optional[List[str]] = None):
        self.base_path = Path(base_path) if base_path else Path.cwd()
        self.allowed_commands = allowed_commands or ["python", "pip", "git", "npm", "node", "ls", "dir", "cat", "echo"]
        self._timeout = 300

    def check_safety(self, command: str) -> Tuple[bool, str]:
        command_lower = command.lower().strip()
        
        for pattern in self.DANGEROUS_PATTERNS:
            if re.search(pattern, command_lower):
                return False, f"Dangerous pattern detected: {pattern}"
        
        parts = shlex.split(command) if not os.name == 'nt' else command.split()
        if not parts:
            return False, "Empty command"
        
        cmd = parts[0].lower()
        
        if cmd in ["python", "pip", "git", "npm", "node"]:
            return True, "Allowed"
        
        if cmd in ["ls", "dir", "cat", "echo", "cd", "pwd", "type", "mkdir"]:
            return True, "Allowed"
        
        if self.allowed_commands and cmd in [c.lower() for c in self.allowed_commands]:
            return True, "Allowed"
        
        return False, f"Command not allowed: {cmd}"

    def execute(
        self,
        command: str,
        timeout: Optional[int] = None,
        capture_output: bool = True,
        shell: bool = True
    ) -> Dict[str, Any]:
        safe, msg = self.check_safety(command)
        if not safe:
            return {
                "success": False,
                "error": f"Command not allowed: {msg}",
                "command": command
            }
        
        try:
            timeout = timeout or self._timeout
            
            if os.name == 'nt':
                result = subprocess.run(
                    command,
                    capture_output=capture_output,
                    shell=True,
                    timeout=timeout,
                    cwd=str(self.base_path),
                    text=True
                )
            else:
                result = subprocess.run(
                    command,
                    capture_output=capture_output,
                    shell=True,
                    timeout=timeout,
                    cwd=str(self.base_path),
                    text=True
                )
            
            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout if capture_output else "",
                "stderr": result.stderr if capture_output else "",
                "command": command
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": f"Command timed out after {timeout} seconds",
                "command": command
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "command": command
            }

    def execute_python(self, code: str, timeout: Optional[int] = None) -> Dict[str, Any]:
        try:
            import tempfile
            
            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
                f.write(code)
                temp_path = f.name
            
            try:
                result = subprocess.run(
                    ["python", temp_path],
                    capture_output=True,
                    timeout=timeout or self._timeout,
                    text=True
                )
                
                return {
                    "success": result.returncode == 0,
                    "returncode": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }
            finally:
                os.unlink(temp_path)
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def run_python_script(self, script_path: str, args: List[str] = None) -> Dict[str, Any]:
        try:
            script_path = Path(script_path)
            if not script_path.exists():
                return {"success": False, "error": f"Script not found: {script_path}"}
            
            cmd = ["python", str(script_path)]
            if args:
                cmd.extend(args)
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=self._timeout,
                text=True,
                cwd=str(script_path.parent)
            )
            
            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def get_environment_info(self) -> Dict[str, Any]:
        return {
            "platform": os.name,
            "cwd": str(self.base_path),
            "path": os.environ.get("PATH", "").split(os.pathsep),
            "python_version": os.environ.get("PYTHON_VERSION", "unknown")
        }

    def list_processes(self) -> Dict[str, Any]:
        try:
            if os.name == 'nt':
                result = subprocess.run(
                    ["tasklist"],
                    capture_output=True,
                    text=True
                )
            else:
                result = subprocess.run(
                    ["ps", "aux"],
                    capture_output=True,
                    text=True
                )
            
            return {
                "success": True,
                "processes": result.stdout
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
