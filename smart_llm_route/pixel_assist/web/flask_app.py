from flask import Flask, render_template, request, jsonify, session
from flask_session import Session
import uuid
import asyncio
from pathlib import Path

from ..chat import PixelChat, ChatRequest, create_pixel_chat
from ..session import SessionManager
from ..history import ChatHistory
from ..tools.runner import ToolRunner
from ..custom_provider import CustomModelProvider


def create_flask_app(config: dict = None, template_folder: str = None, static_folder: str = None):
    app = Flask(__name__, template_folder=template_folder, static_folder=static_folder)
    app.secret_key = str(uuid.uuid4())
    
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_PERMANENT'] = False
    app.config['SESSION_USE_SIGNER'] = True
    Session(app)
    
    pixel_chat = create_pixel_chat(config)
    session_manager = SessionManager()
    chat_history = ChatHistory()
    tool_runner = ToolRunner(allow_execution=True)
    
    @app.route('/')
    def index():
        if 'session_id' not in session:
            session['session_id'] = str(uuid.uuid4())
        return render_template('index.html')
    
    @app.route('/api/chat', methods=['POST'])
    def chat():
        data = request.get_json()
        message = data.get('message', '')
        session_id = data.get('session_id', session.get('session_id'))
        model_preference = data.get('model_preference')
        
        if not message:
            return jsonify({'error': 'Empty message'}), 400
        
        async def get_response():
            request_obj = ChatRequest(
                message=message,
                session_id=session_id,
                tools_enabled=True,
                model_preference=model_preference
            )
            return await pixel_chat.chat(request_obj)
        
        response = asyncio.run(get_response())
        
        return jsonify({
            'message': response.message,
            'session_id': response.session_id,
            'model_used': response.model_used,
            'cost': response.cost
        })
    
    @app.route('/api/session', methods=['GET', 'POST', 'DELETE'])
    def handle_session():
        if request.method == 'GET':
            sessions = chat_history.list_sessions(20)
            return jsonify(sessions)
        
        elif request.method == 'POST':
            session_id = request.get_json().get('session_id')
            if session_id:
                session['session_id'] = session_id
                return jsonify({'success': True})
            return jsonify({'error': 'No session_id'}), 400
        
        elif request.method == 'DELETE':
            session_id = request.get_json().get('session_id')
            if session_id and chat_history.delete_session(session_id):
                return jsonify({'success': True})
            return jsonify({'error': 'Session not found'}), 404
    
    @app.route('/api/tools', methods=['GET'])
    def list_tools():
        return jsonify(tool_runner.list_tools())
    
    @app.route('/api/tools/execute', methods=['POST'])
    def execute_tool():
        data = request.get_json()
        tool_name = data.get('tool')
        args = data.get('args', {})
        
        if not tool_name:
            return jsonify({'error': 'No tool specified'}), 400
        
        result = tool_runner.run_tool(tool_name, **args)
        
        return jsonify({
            'tool': result.tool,
            'success': result.success,
            'result': result.result,
            'error': result.error
        })
    
    @app.route('/api/stats', methods=['GET'])
    def stats():
        return jsonify(pixel_chat.get_stats())
    
    @app.route('/api/models', methods=['GET'])
    def list_models():
        return jsonify(pixel_chat.list_available_models())
    
    @app.route('/api/instructions', methods=['GET'])
    def get_instructions():
        return jsonify({
            'current': pixel_chat.instructions,
            'system_prompts': pixel_chat.get_system_prompts(),
            'rules': pixel_chat.get_rules()
        })
    
    @app.route('/api/instructions', methods=['POST'])
    def update_instructions():
        data = request.get_json()
        
        if data.get('instructions'):
            pixel_chat.set_instructions(data['instructions'])
            return jsonify({'success': True, 'message': 'Instructions updated'})
        
        if data.get('system_prompt'):
            success = pixel_chat.set_system_prompt(data['system_prompt'])
            if success:
                return jsonify({'success': True, 'message': f"System prompt set to {data['system_prompt']}"})
            return jsonify({'success': False, 'error': 'Invalid system prompt name'})
        
        if data.get('rule'):
            if data.get('action') == 'remove':
                success = pixel_chat.remove_rule(data['rule'])
                if success:
                    return jsonify({'success': True, 'message': 'Rule removed'})
            else:
                success = pixel_chat.add_rule(data['rule'])
                if success:
                    return jsonify({'success': True, 'message': 'Rule added'})
            return jsonify({'success': False, 'error': 'Rule not found'})
        
        return jsonify({'success': False, 'error': 'No valid action provided'})
    
    @app.route('/api/custom-models', methods=['GET'])
    def list_custom_models():
        from ..custom_provider import get_registry
        registry = get_registry()
        return jsonify(registry.list_models())
    
    @app.route('/api/custom-models', methods=['POST'])
    def create_custom_model():
        data = request.get_json()
        from ..custom_provider import get_registry
        registry = get_registry()
        
        registry.register_model(data['name'], data)
        return jsonify({'success': True, 'message': f"Model {data['name']} registered"})
    
    @app.route('/api/custom-models/<model_name>', methods=['DELETE'])
    def delete_custom_model(model_name):
        from ..custom_provider import get_registry
        registry = get_registry()
        
        if registry.unregister_model(model_name):
            return jsonify({'success': True, 'message': f"Model {model_name} removed"})
        return jsonify({'success': False, 'error': 'Model not found'})
    
    @app.route('/api/custom-models/discover', methods=['GET'])
    def discover_local_models():
        from ..custom_provider import CustomModelProvider
        
        configs = [
            {"name": "ollama", "base_url": "http://localhost:11434", "endpoint": "/api/generate", "provider": "local"},
            {"name": "lmstudio", "base_url": "http://localhost:1234", "endpoint": "/v1/chat/completions", "provider": "openai-compatible"},
        ]
        
        discovered = []
        for config in configs:
            provider = CustomModelProvider(config)
            import asyncio
            models = asyncio.run(provider.list_models())
            if models:
                discovered.append({
                    "server": config["name"],
                    "base_url": config["base_url"],
                    "models": models
                })
        
        return jsonify(discovered)
    
    return app


def run_flask_app(host: str = '127.0.0.1', port: int = 5000, **kwargs):
    app = create_flask_app(**kwargs)
    app.run(host=host, port=port, debug=True)


if __name__ == '__main__':
    run_flask_app()
