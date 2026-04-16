"""Example usage of Smart LLM Route."""
import asyncio
from smart_llm_route.models.registry import ModelRegistry
from smart_llm_route.core.router import SmartRouter
from smart_llm_route.learning.tracker import PerformanceTracker
from smart_llm_route.learning.optimizer import RouteOptimizer
from smart_llm_route.skills.registry import SkillRegistry
from smart_llm_route.skills.executor import SkillExecutor
from smart_llm_route.costs.tracker import CostTracker

def create_router():
    registry = ModelRegistry()
    
    registry.register_model("gpt-4", "openai", 0.03, ["coding", "reasoning", "creative"])
    registry.register_model("gpt-3.5-turbo", "openai", 0.002, ["simple_coding", "basic_reasoning"])
    registry.register_model("claude-3-opus", "anthropic", 0.015, ["coding", "reasoning", "creative"])
    registry.register_model("llama2", "local", 0.0, ["simple_coding", "basic_reasoning"])
    
    return registry

async def basic_example():
    print("=== Basic Router Example ===")
    registry = create_router()
    router = SmartRouter(registry)
    
    result = await router.route(
        task_description="Write a hello world function in Python",
        task_type="coding",
        budget=0.5
    )
    
    print(f"Model: {result['model']}")
    print(f"Response: {result['response']['content']}")
    print()

async def learning_example():
    print("=== Learning System Example ===")
    registry = create_router()
    tracker = PerformanceTracker()
    optimizer = RouteOptimizer(registry, tracker)
    
    tracker.record_request(
        task_type="coding",
        task_description="Write a function",
        model="gpt-4",
        provider="openai",
        success=True,
        latency_ms=1500.0,
        cost=0.01
    )
    
    task_perf = tracker.get_task_performance("coding")
    print(f"Best model for coding: {task_perf['best_model']}")
    print(f"Model scores: {task_perf['model_scores']}")
    print()

async def skills_example():
    print("=== Skills Example ===")
    registry = create_router()
    skill_registry = SkillRegistry()
    skill_executor = SkillExecutor(skill_registry, registry)
    
    skill = skill_executor.determine_skill_from_prompt("Write a hello world function in Python")
    print(f"Detected skill: {skill.name if skill else 'unknown'}")
    print()

async def cost_example():
    print("=== Cost Tracking Example ===")
    registry = create_router()
    tracker = CostTracker()
    
    tracker.set_budget("myproject", 10.0)
    tracker.add_cost(0.05, "gpt-4", "myproject")
    
    budget_status = tracker.check_budget("myproject")
    print(f"Budget status: {budget_status}")
    print(f"Total spending: ${tracker.get_total_spending():.2f}")
    print()

async def main():
    await basic_example()
    await learning_example()
    await skills_example()
    await cost_example()
    print("All examples completed!")

if __name__ == "__main__":
    asyncio.run(main())