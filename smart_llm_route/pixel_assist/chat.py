import asyncio
import uuid
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

from ..core.router import SmartRouter
from ..models.registry import ModelRegistry
from .instructions import instruction_manager, DEFAULT_INSTRUCTIONS
from .custom_provider import get_registry as get_custom_registry, CustomModelProvider


@dataclass
class Message:
    role: str
    content: str
    timestamp: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.timestamp:
            from datetime import datetime
            self.timestamp = datetime.now().isoformat()


@dataclass
class ChatRequest:
    message: str
    session_id: Optional[str] = None
    model_preference: Optional[str] = None
    task_type: str = "general"
    budget: float = 0.5
    tools_enabled: bool = True


@dataclass
class ChatResponse:
    message: str
    session_id: str
    model_used: str
    cost: float
    tools_used: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class PixelChat:
    def __init__(
        self,
        registry: ModelRegistry,
        use_learning: bool = True,
        security=None,
        client_id: str = "pixel_assist"
    ):
        self.registry = registry
        self.router = SmartRouter(registry, use_learning, security, client_id)
        self.sessions: Dict[str, List[Message]] = {}
        self.default_task_type = "general"
        self.default_budget = 0.5
        self.instructions = instruction_manager.get_full_prompt()

    def set_instructions(self, instructions: str):
        instruction_manager.set_custom_instructions(instructions)
        self.instructions = instruction_manager.get_full_prompt()

    def set_system_prompt(self, name: str) -> bool:
        result = instruction_manager.set_system_prompt(name)
        if result:
            self.instructions = instruction_manager.get_full_prompt()
        return result

    def add_rule(self, rule: str) -> bool:
        result = instruction_manager.add_rule(rule)
        if result:
            self.instructions = instruction_manager.get_full_prompt()
        return result

    def remove_rule(self, rule: str) -> bool:
        result = instruction_manager.remove_rule(rule)
        if result:
            self.instructions = instruction_manager.get_full_prompt()
        return result

    def get_system_prompts(self) -> Dict[str, str]:
        return instruction_manager.get_system_prompts()

    def get_rules(self) -> List[str]:
        return instruction_manager.get_rules()

    async def chat(self, request: ChatRequest) -> ChatResponse:
        session_id = request.session_id or str(uuid.uuid4())
        
        if session_id not in self.sessions:
            self.sessions[session_id] = []

        user_message = Message(role="user", content=request.message)
        self.sessions[session_id].append(user_message)

        full_prompt = self.instructions
        if request.message:
            full_prompt = f"{full_prompt}\n\nUser request: {request.message}"
        
        messages = self._build_context(session_id)
        
        task_type = request.task_type or self.default_task_type
        budget = request.budget or self.default_budget
        
        model_override = request.model_preference
        
        custom_registry = get_custom_registry()
        custom_model_config = custom_registry.get_model_config(model_override) if model_override else None
        
        if not custom_model_config:
            models = self.list_available_models()
            for m in models:
                if m.get("name") == model_override and m.get("base_url"):
                    custom_registry.register_model(model_override, m)
                    custom_model_config = m
                    break
        
        if custom_model_config:
            provider = custom_registry.get_provider(model_override)
            if provider:
                try:
                    response = await provider.generate(
                        model=model_override,
                        prompt=request.message,
                        system_prompt=self.instructions
                    )
                    
                    assistant_message = Message(
                        role="assistant",
                        content=response["content"],
                        metadata={"model": model_override, "custom": True}
                    )
                    self.sessions[session_id].append(assistant_message)
                    
                    return ChatResponse(
                        message=response["content"],
                        session_id=session_id,
                        model_used=model_override,
                        cost=0.0,
                        metadata=response
                    )
                except Exception as e:
                    return ChatResponse(
                        message=f"Error with custom model: {str(e)}",
                        session_id=session_id,
                        model_used=model_override,
                        cost=0.0
                    )
        
        try:
            result = await self.router.route(
                task_description=full_prompt,
                task_type=task_type,
                budget=budget,
                model_override=model_override
            )
            
            assistant_message = Message(
                role="assistant",
                content=result["response"]["content"],
                metadata={"model": result["model"]}
            )
            self.sessions[session_id].append(assistant_message)

            return ChatResponse(
                message=result["response"]["content"],
                session_id=session_id,
                model_used=result["model"],
                cost=result["response"].get("cost", 0.0),
                metadata=result.get("response", {})
            )
        except Exception as e:
            error_message = Message(
                role="assistant",
                content=f"Error: {str(e)}",
                metadata={"error": True}
            )
            self.sessions[session_id].append(error_message)
            
            return ChatResponse(
                message=f"Error: {str(e)}",
                session_id=session_id,
                model_used="none",
                cost=0.0
            )

    def _build_context(self, session_id: str) -> List[Message]:
        return self.sessions.get(session_id, [])

    def get_session(self, session_id: str) -> List[Message]:
        return self.sessions.get(session_id, [])

    def list_sessions(self) -> List[str]:
        return list(self.sessions.keys())

    def delete_session(self, session_id: str) -> bool:
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False

    def get_stats(self) -> Dict[str, Any]:
        stats = self.router.get_stats()
        stats["sessions"] = len(self.sessions)
        stats["total_messages"] = sum(len(m) for m in self.sessions.values())
        return stats

    def list_available_models(self) -> List[Dict[str, Any]]:
        custom_registry = get_custom_registry()
        custom_models = custom_registry.list_models()
        
        if custom_models:
            return custom_models
        
        return [
            {
                "name": "llama2",
                "provider": "local",
                "cost_per_1k": 0.0,
                "capabilities": ["general", "coding"],
                "description": "Llama 2 - Add your model URL to use",
                "base_url": "http://localhost:11434",
                "endpoint": "/api/generate"
            },
            {
                "name": "mistral",
                "provider": "local",
                "cost_per_1k": 0.0,
                "capabilities": ["general", "coding"],
                "description": "Mistral - Add your model URL to use",
                "base_url": "http://localhost:11434",
                "endpoint": "/api/generate"
            },
            {
                "name": "codellama",
                "provider": "local",
                "cost_per_1k": 0.0,
                "capabilities": ["coding", "reasoning"],
                "description": "Code Llama - For coding tasks",
                "base_url": "http://localhost:11434",
                "endpoint": "/api/generate"
            }
        ]


def create_pixel_chat(config: dict = None) -> PixelChat:
    from ..cli.main import init_registry
    
    if config is None:
        from ..cli.main import load_config
        config = load_config()
    
    registry = init_registry(config)
    return PixelChat(registry)
