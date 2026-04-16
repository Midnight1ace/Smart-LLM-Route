from typing import Optional
from .registry import Skill, SkillRegistry
from ..models.registry import ModelRegistry, ModelMetadata

class SkillExecutor:
    def __init__(self, skill_registry: SkillRegistry, model_registry: ModelRegistry):
        self.skill_registry = skill_registry
        self.model_registry = model_registry

    def determine_skill_from_prompt(self, prompt: str) -> Optional[Skill]:
        prompt_lower = prompt.lower()
        skills = self.skill_registry.list_skills()
        
        for skill in skills:
            for example in skill.example_prompts:
                if example.lower() in prompt_lower:
                    return skill
        
        for skill in skills:
            if skill.description.lower() in prompt_lower:
                return skill
        
        return skills[0] if skills else None

    def get_best_model_for_skill(
        self, 
        skill: Skill, 
        max_budget: float,
        task_performance: Optional[dict] = None
    ) -> Optional[ModelMetadata]:
        candidates = []
        for cap in skill.preferred_capabilities:
            candidates.extend(self.model_registry.list_models_by_capability(cap))
        
        if not candidates:
            return None
        
        if task_performance:
            model_scores = task_performance.get("model_scores", {})
            for model in candidates:
                score = model_scores.get(model.name, {}).get("rate", 0.5)
                if score >= 0.5:
                    return model
        
        affordable = [m for m in candidates if m.cost_per_1k <= max_budget]
        if not affordable:
            return min(candidates, key=lambda x: x.cost_per_1k)
        
        return min(affordable, key=lambda x: x.cost_per_1k)