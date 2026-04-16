import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime


SYSTEM_PROMPTS = {
    "default": "You are Pixel-assist, a helpful AI coding assistant.",
    "developer": "You are a expert software developer. Help write clean, well-documented code.",
    "reviewer": "You are a code reviewer. Provide constructive feedback on code quality.",
    "debugger": "You are a debugging expert. Help identify and fix bugs in code.",
    "docs": "You are a technical documentation writer. Create clear documentation.",
    "custom": ""
}

DEFAULT_INSTRUCTIONS = """You are Pixel-assist, a helpful AI coding assistant.
- Help users write, debug, and understand code
- Provide clear explanations
- Suggest best practices when applicable
- If you need more information, ask clarifying questions"""


class InstructionManager:
    def __init__(self, storage_path: Optional[str] = None):
        if storage_path:
            self.storage_path = Path(storage_path)
        else:
            self.storage_path = Path.home() / ".pixel_assist" / "instructions"
        
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.instructions_file = self.storage_path / "instructions.json"
        self._load()

    def _load(self):
        if self.instructions_file.exists():
            try:
                with open(self.instructions_file, "r") as f:
                    data = json.load(f)
                    self.custom_instructions = data.get("custom", DEFAULT_INSTRUCTIONS)
                    self.system_prompt = data.get("system_prompt", "default")
                    self.rules = data.get("rules", [])
            except Exception:
                self._reset()
        else:
            self._reset()

    def _reset(self):
        self.custom_instructions = DEFAULT_INSTRUCTIONS
        self.system_prompt = "default"
        self.rules = []

    def _save(self):
        try:
            with open(self.instructions_file, "w") as f:
                json.dump({
                    "custom": self.custom_instructions,
                    "system_prompt": self.system_prompt,
                    "rules": self.rules
                }, f, indent=2)
        except Exception:
            pass

    def get_system_prompts(self) -> Dict[str, str]:
        prompts = dict(SYSTEM_PROMPTS)
        prompts["custom"] = self.custom_instructions
        return prompts

    def get_current_instructions(self) -> str:
        if self.system_prompt == "custom":
            return self.custom_instructions
        return SYSTEM_PROMPTS.get(self.system_prompt, SYSTEM_PROMPTS["default"])

    def set_system_prompt(self, name: str) -> bool:
        if name in SYSTEM_PROMPTS:
            self.system_prompt = name
            self._save()
            return True
        return False

    def set_custom_instructions(self, instructions: str) -> bool:
        self.custom_instructions = instructions
        self.system_prompt = "custom"
        self._save()
        return True

    def add_rule(self, rule: str) -> bool:
        if rule not in self.rules:
            self.rules.append(rule)
            self._save()
            return True
        return False

    def remove_rule(self, rule: str) -> bool:
        if rule in self.rules:
            self.rules.remove(rule)
            self._save()
            return True
        return False

    def get_rules(self) -> List[str]:
        return self.rules.copy()

    def get_full_prompt(self) -> str:
        instructions = self.get_current_instructions()
        rules = self.get_rules()
        
        if rules:
            rules_text = "\n".join(f"- {r}" for r in rules)
            return f"{instructions}\n\nAdditional Rules:\n{rules_text}"
        return instructions


instruction_manager = InstructionManager()
