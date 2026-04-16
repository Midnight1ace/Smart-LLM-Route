from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class Skill:
    name: str
    description: str
    preferred_capabilities: List[str]
    example_prompts: List[str] = field(default_factory=list)
    required: bool = False

class SkillRegistry:
    def __init__(self):
        self.skills: dict[str, Skill] = {}
        self._load_default_skills()

    def _load_default_skills(self):
        default_skills = [
            Skill(
                name="coding",
                description="Write, debug, or explain code",
                preferred_capabilities=["coding"],
                example_prompts=["Write a hello world", "Fix this bug"]
            ),
            Skill(
                name="reasoning",
                description="Logical reasoning and analysis",
                preferred_capabilities=["reasoning"],
                example_prompts=["Explain why", "Analyze this"]
            ),
            Skill(
                name="creative",
                description="Creative writing, brainstorming",
                preferred_capabilities=["creative"],
                example_prompts=["Write a story", "Brainstorm ideas"]
            ),
            Skill(
                name="simple_coding",
                description="Simple coding tasks",
                preferred_capabilities=["simple_coding"],
                example_prompts=["print hello", "basic function"]
            ),
            Skill(
                name="basic_reasoning",
                description="Basic reasoning tasks",
                preferred_capabilities=["basic_reasoning"],
                example_prompts=["what is 2+2", "simple math"]
            )
        ]
        for skill in default_skills:
            self.skills[skill.name] = skill

    def register_skill(self, skill: Skill):
        self.skills[skill.name] = skill

    def get_skill(self, name: str) -> Optional[Skill]:
        return self.skills.get(name)

    def list_skills(self) -> List[Skill]:
        return list(self.skills.values())