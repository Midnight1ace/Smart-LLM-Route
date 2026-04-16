import asyncio
import os
import sys
from pathlib import Path
from typing import Optional

from ..chat import PixelChat, ChatRequest, create_pixel_chat
from ..session import SessionManager
from ..history import ChatHistory
from ..tools.runner import ToolRunner


WELCOME = """
╔══════════════════════════════════════════════════════════╗
║                    Pixel-assist v1.0                     ║
║              Your AI Coding Assistant                    ║
╚══════════════════════════════════════════════════════════╝

Type your message or /help for commands.
"""

COMMANDS = """
/help, /h        - Show this help message
/exit, /quit     - Exit Pixel-assist
/clear, /c       - Clear the screen
/new, /n         - Start a new chat session
/list, /l        - List all sessions
/load <id>       - Load a session by ID
/delete <id>     - Delete a session
/read <path>     - Read a file
/edit <path>     - Edit a file
/run <cmd>       - Run a shell command
/history         - Show chat history
/stats           - Show usage statistics
/tools           - List available tools
"""


class InteractiveChat:
    def __init__(self, config: Optional[dict] = None):
        self.pixel_chat = create_pixel_chat(config)
        self.session_manager = SessionManager()
        self.history = ChatHistory()
        self.tool_runner = ToolRunner(allow_execution=True)
        self.current_session = None

    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def print_welcome(self):
        self.clear_screen()
        print(WELCOME)

    async def handle_message(self, message: str) -> str:
        request = ChatRequest(
            message=message,
            session_id=self.current_session.id if self.current_session else None,
            tools_enabled=True
        )
        
        response = await self.pixel_chat.chat(request)
        
        if not self.current_session:
            self.current_session = self.session_manager.get_session(response.session_id)
            if not self.current_session:
                self.current_session = self.session_manager.create_session()
                self.current_session.id = response.session_id
        
        return response.message

    async def handle_command(self, cmd: str) -> Optional[str]:
        parts = cmd.strip().split(maxsplit=1)
        command = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        if command in ["/help", "/h"]:
            return COMMANDS
        
        elif command in ["/exit", "/quit"]:
            print("Goodbye!")
            sys.exit(0)
        
        elif command in ["/clear", "/c"]:
            self.clear_screen()
            print(WELCOME)
            return None
        
        elif command in ["/new", "/n"]:
            self.current_session = self.session_manager.create_session()
            return "New chat session started."
        
        elif command in ["/list", "/l"]:
            sessions = self.history.list_sessions(20)
            if not sessions:
                return "No sessions found."
            lines = ["Sessions:"]
            for s in sessions:
                lines.append(f"  {s['id'][:8]} - {s['title']} ({s['message_count']} messages)")
            return "\n".join(lines)
        
        elif command == "/load":
            if not args:
                return "Usage: /load <session_id>"
            session = self.history.load_session(args)
            if session:
                self.current_session = session
                return f"Loaded session: {session.title}"
            return f"Session not found: {args}"
        
        elif command == "/delete":
            if not args:
                return "Usage: /delete <session_id>"
            if self.history.delete_session(args):
                if self.current_session and self.current_session.id == args:
                    self.current_session = self.session_manager.create_session()
                return "Session deleted."
            return f"Session not found: {args}"
        
        elif command == "/read":
            if not args:
                return "Usage: /read <file_path>"
            result = self.tool_runner.run_tool("read_file", path=args)
            if result.success:
                content = result.result.get("content", "")
                lines = content.split("\n")[:50]
                return f"File: {args}\n" + "\n".join(f"{i+1}: {l}" for i, l in enumerate(lines))
            return f"Error: {result.error}"
        
        elif command == "/edit":
            return "Usage: /edit <file_path> <old> <new> (not yet implemented)"
        
        elif command == "/run":
            if not args:
                return "Usage: /run <command>"
            result = self.tool_runner.run_tool("execute", command=args)
            if result.success:
                output = result.result.get("stdout", "")
                error = result.result.get("stderr", "")
                return f"Output:\n{output}\n" + (f"Error:\n{error}" if error else "")
            return f"Error: {result.error}"
        
        elif command == "/history":
            if not self.current_session:
                return "No active session."
            messages = self.current_session.get_messages()
            if not messages:
                return "No messages in this session."
            lines = ["Chat history:"]
            for m in messages:
                lines.append(f"\n{m['role']}: {m['content'][:100]}...")
            return "\n".join(lines)
        
        elif command == "/stats":
            stats = self.pixel_chat.get_stats()
            return f"Sessions: {stats.get('sessions', 0)}\nTotal messages: {stats.get('total_messages', 0)}"
        
        elif command == "/tools":
            tools = self.tool_runner.list_tools()
            return "Available tools:\n  " + "\n  ".join(tools)
        
        return None

    async def chat_loop(self):
        self.print_welcome()
        
        self.current_session = self.session_manager.create_session("Main Chat")
        
        while True:
            try:
                user_input = input("\nYou: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.startswith("/"):
                    response = await self.handle_command(user_input)
                    if response:
                        print(f"\n{response}")
                    continue
                
                response = await self.handle_message(user_input)
                print(f"\nPixel: {response}")
                
            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                print(f"\nError: {e}")


async def main():
    chat = InteractiveChat()
    await chat.chat_loop()


if __name__ == "__main__":
    asyncio.run(main())
