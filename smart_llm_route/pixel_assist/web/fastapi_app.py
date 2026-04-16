from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
import uuid
import asyncio
from pathlib import Path

from ..chat import PixelChat, ChatRequest, create_pixel_chat
from ..session import SessionManager
from ..history import ChatHistory
from ..tools.runner import ToolRunner


app = FastAPI(title="Pixel-assist")

static_path = Path(__file__).parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

pixel_chat = None
session_manager = SessionManager()
chat_history = ChatHistory()
tool_runner = ToolRunner(allow_execution=True)

sessions_store: Dict[str, Any] = {}


class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None
    model_preference: Optional[str] = None


class ToolExecute(BaseModel):
    tool: str
    args: Dict[str, Any] = {}


class SessionCreate(BaseModel):
    session_id: Optional[str] = None


def get_chat():
    global pixel_chat
    if pixel_chat is None:
        pixel_chat = create_pixel_chat()
    return pixel_chat


@app.get("/", response_class=HTMLResponse)
async def read_root():
    template_path = Path(__file__).parent / "templates" / "index.html"
    if template_path.exists():
        return template_path.read_text()
    return "<h1>Pixel-assist API</h1><p>Status: running</p>"


@app.post("/api/chat")
async def chat(message: ChatMessage):
    chat = get_chat()
    
    session_id = message.session_id or str(uuid.uuid4())
    
    request_obj = ChatRequest(
        message=message.message,
        session_id=session_id,
        tools_enabled=True,
        model_preference=message.model_preference
    )
    
    response = await chat.chat(request_obj)
    
    return {
        "message": response.message,
        "session_id": response.session_id,
        "model_used": response.model_used,
        "cost": response.cost
    }


@app.get("/api/sessions")
async def list_sessions():
    return chat_history.list_sessions(20)


@app.post("/api/sessions")
async def create_session(data: SessionCreate):
    session_id = data.session_id or str(uuid.uuid4())
    sessions_store[session_id] = {"id": session_id}
    return {"session_id": session_id}


@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    if chat_history.delete_session(session_id):
        return {"success": True}
    raise HTTPException(status_code=404, detail="Session not found")


@app.get("/api/tools")
async def list_tools():
    return tool_runner.list_tools()


@app.get("/api/models")
async def list_models():
    chat = get_chat()
    return chat.list_available_models()


@app.post("/api/tools/execute")
async def execute_tool(data: ToolExecute):
    result = tool_runner.run_tool(data.tool, **data.args)
    
    return {
        "tool": result.tool,
        "success": result.success,
        "result": result.result,
        "error": result.error
    }


@app.get("/api/stats")
async def get_stats():
    chat = get_chat()
    return chat.get_stats()


@app.get("/api/instructions")
async def get_instructions():
    chat = get_chat()
    return {
        "current": chat.instructions,
        "system_prompts": chat.get_system_prompts(),
        "rules": chat.get_rules()
    }


class InstructionsUpdate(BaseModel):
    instructions: Optional[str] = None
    system_prompt: Optional[str] = None
    rule: Optional[str] = None
    action: Optional[str] = None


@app.post("/api/instructions")
async def update_instructions(data: InstructionsUpdate):
    chat = get_chat()
    
    if data.instructions:
        chat.set_instructions(data.instructions)
        return {"success": True, "message": "Instructions updated"}
    
    if data.system_prompt:
        success = chat.set_system_prompt(data.system_prompt)
        if success:
            return {"success": True, "message": f"System prompt set to {data.system_prompt}"}
        return {"success": False, "error": "Invalid system prompt name"}
    
    if data.rule:
        if data.action == "remove":
            success = chat.remove_rule(data.rule)
            if success:
                return {"success": True, "message": "Rule removed"}
        else:
            success = chat.add_rule(data.rule)
            if success:
                return {"success": True, "message": "Rule added"}
        return {"success": False, "error": "Rule not found"}
    
    return {"success": False, "error": "No valid action provided"}


def run_fastapi_app(host: str = '127.0.0.1', port: int = 8000):
    import uvicorn
    uvicorn.run(app, host=host, port=port)


class CustomModelCreate(BaseModel):
    name: str
    base_url: str
    endpoint: str = "/api/generate"
    api_key: str = ""
    provider: str = "local"
    capabilities: List[str] = ["general", "coding"]
    cost_per_1k: float = 0.0
    description: str = ""
    context_length: int = 4096


@app.get("/api/custom-models")
async def list_custom_models():
    from ..custom_provider import get_registry
    registry = get_registry()
    return registry.list_models()


@app.post("/api/custom-models")
async def create_custom_model(model: CustomModelCreate):
    from ..custom_provider import get_registry, CustomModelProvider
    registry = get_registry()
    
    config = model.model_dump()
    registry.register_model(model.name, config)
    
    return {"success": True, "message": f"Model {model.name} registered"}


@app.delete("/api/custom-models/{model_name}")
async def delete_custom_model(model_name: str):
    from ..custom_provider import get_registry
    registry = get_registry()
    
    if registry.unregister_model(model_name):
        return {"success": True, "message": f"Model {model_name} removed"}
    return {"success": False, "error": "Model not found"}


@app.get("/api/custom-models/discover")
async def discover_local_models():
    from ..custom_provider import CustomModelProvider
    
    configs = [
        {"name": "ollama", "base_url": "http://localhost:11434", "endpoint": "/api/generate", "provider": "local"},
        {"name": "lmstudio", "base_url": "http://localhost:1234", "endpoint": "/v1/chat/completions", "provider": "openai-compatible"},
        {"name": "ollama-litellm", "base_url": "http://localhost:4000", "endpoint": "/v1/chat/completions", "provider": "openai-compatible"},
    ]
    
    discovered = []
    for config in configs:
        provider = CustomModelProvider(config)
        models = await provider.list_models()
        if models:
            discovered.append({
                "server": config["name"],
                "base_url": config["base_url"],
                "models": models
            })
    
    return discovered


if __name__ == "__main__":
    run_fastapi_app()
