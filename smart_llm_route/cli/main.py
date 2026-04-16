import asyncio
import yaml
from pathlib import Path
from ..models.registry import ModelRegistry
from ..core.router import SmartRouter

def load_config() -> dict:
    config_path = Path(__file__).parent.parent / "config.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)

def init_registry(config: dict) -> ModelRegistry:
    registry = ModelRegistry()
    for model_name, model_config in config.get("models", {}).items():
        registry.register_model(
            name=model_name,
            provider=model_config["provider"],
            cost=model_config["cost_per_1k"],
            capabilities=model_config["capabilities"]
        )
    return registry

async def main():
    config = load_config()
    registry = init_registry(config)
    
    router = SmartRouter(registry)
    
    result = await router.route(
        task_description="Write a hello world function in Python",
        task_type="coding",
        budget=0.5
    )
    
    print(f"Model: {result['model']}")
    print(f"Response: {result['response']['content']}")

if __name__ == "__main__":
    asyncio.run(main())