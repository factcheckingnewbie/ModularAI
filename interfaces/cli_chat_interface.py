#!/usr/bin/env python3
"""
Command-line interface for user interaction.

Features:
- Presents interface menu
- Handles non-blocking user input
- Can support multiple simultaneous connections
"""

import asyncio
import json
import sys
import os
from asyncio import StreamReader, StreamWriter


class CliP:
    """
    """
    
    def __init__(self):
        self.connected_models = {}
        self.active_model = None
        self.reader = None
        self.writer = None
        self.running = True
        self.command_history = []
        self.history_size = 100
        self.prompt_symbol = "> "
        self.tasks = set()
        
    def get_interface_id(self):
        """Return the interface ID for compatibility checking."""
        return "chat_interface"
        
    async def setup_streams(self, reader, writer):
        """
        Set up the StreamReader and StreamWriter for communication.
        
        Args:
            reader (StreamReader): For receiving data from the module controller
            writer (StreamWriter): For sending data to the module controller
        """
        self.reader = reader
        self.writer = writer
        
        # Set up the first model connection (initially there's only one)
        model_id = "default"
        self.connected_models[model_id] = {
            "reader": reader,
            "writer": writer,
            "name": "AI Model",
            "active": True
        }
        self.active_model = model_id
        
    async def get_capabilities(self):
        """
        Return the capabilities of this interface for compatibility checking.
        
        Returns:
            dict: Interface capabilities
        """
        return {
            "required_capabilities": ["text_io"],
            "optional_capabilities": ["structured_output"]
        }
        
    async def display_welcome(self):
        """Display welcome message and basic instructions."""
        welcome = """
╔════════════════════════════════════════════════════════╗
║                 ModdularAI Chat Interface               ║
╠════════════════════════════════════════════════════════╣
║ Commands:                                              ║
║  /help           - Show this help message              ║
║  /quit, /exit    - Exit the program                    ║
║  /models         - List connected models               ║
║  /switch <id>    - Switch to a different model         ║
║  /clear          - Clear the screen                    ║
║                                                        ║
║ Any other input will be sent to the active AI model.   ║
╚════════════════════════════════════════════════════════╝
"""
        print(welcome)
        
    async def display_prompt(self):
        """Display command prompt to the user."""
        if self.active_model and self.active_model in self.connected_models:
            model_name = self.connected_models[self.active_model].get("name", "Model")
            print(f"{model_name} {self.prompt_symbol}", end="", flush=True)
        else:
            print(f"{self.prompt_symbol}", end="", flush=True)
        
    async def handle_input(self):
        """
        Handle user input in a non-blocking manner.
        Reads from stdin and processes commands.
        """
        # Create a StreamReader for stdin
        loop = asyncio.get_running_loop()
        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        
        # Connect the stdin to the StreamReader
        await loop.connect_read_pipe(lambda: protocol, sys.stdin)
        
        try:
            while self.running:
                # Display prompt
                await self.display_prompt()
                
                # Read line from stdin (non-blocking)
                line = await reader.readline()
                command = line.decode().strip()
                
                # Skip empty commands
                if not command:
                    continue
                    
                # Add to history
                self.command_history.append(command)
                if len(self.command_history) > self.history_size:
                    self.command_history.pop(0)
                
                # Process the command
                await self.process_command(command)
                
        except asyncio.CancelledError:
            # Handle cancellation gracefully
            print("\nInput handling cancelled.")
        except Exception as e:
            print(f"\nError in input handling: {e}")
        
    async def process_command(self, command):
        """
        Process a user command.
        
        Args:
            command (str): The command entered by the user
        """
        # Check if it's a special command
        if command.startswith('/'):
            cmd_parts = command.split()
            cmd = cmd_parts[0].lower()
            
            if cmd in ['/quit', '/exit']:
                print("Exiting...")
                self.running = False
                return
                
            elif cmd == '/help':
                await self.display_welcome()
                
            elif cmd == '/models':
                print("\nConnected Models:")
                for model_id, model_info in self.connected_models.items():
                    active = " (active)" if model_id == self.active_model else ""
                    print(f"  - {model_info.get('name', model_id)}{active}")
                    
            elif cmd == '/switch' and len(cmd_parts) > 1:
                model_id = cmd_parts[1]
                if model_id in self.connected_models:
                    self.active_model = model_id
                    print(f"Switched to {self.connected_models[model_id].get('name', model_id)}")
                else:
                    print(f"Model '{model_id}' not found.")
                    
            elif cmd == '/clear':
                os.system('clear' if os.name == 'posix' else 'cls')
                
            else:
                print(f"Unknown command: {cmd}")
        else:
            # Send message to the active model
            await self.send_to_model(command)
        
    async def send_to_model(self, message):
        """
        Send a message to the currently active AI model.
        
        Args:
            message (str): The message to send
        """
        if not self.active_model or self.active_model not in self.connected_models:
            print("No active model to send message to.")
            return
            
        try:
            # Format message as JSON
            msg_obj = {
                "message_type": "text_generation",
                "prompt": message,
                "request_id": f"req_{len(self.command_history)}"
            }
            
            # Convert to JSON string and add newline
            json_msg = json.dumps(msg_obj) + '\n'
            
            # Get writer for active model
            writer = self.connected_models[self.active_model]["writer"]
            
            # Send message
            writer.write(json_msg.encode('utf-8'))
            await writer.drain()
            
        except Exception as e:
            print(f"\nError sending message: {e}")
        
    async def receive_from_model(self):
        """
        Continuously receive and display messages from AI models.
        Non-blocking implementation.
        """
        try:
            while self.running:
                # Process messages from all connected models
                for model_id, model_info in list(self.connected_models.items()):
                    reader = model_info["reader"]
                    
                    # Check if there's data available
                    if not reader.at_eof():
                        try:
                            # Try to read a line with a short timeout
                            data = await asyncio.wait_for(reader.readline(), timeout=0.1)
                            
                            if data:
                                # Process the response
                                await self.handle_model_response(model_id, data)
                            elif reader.at_eof():
                                # Model disconnected
                                print(f"\nModel {model_info.get('name', model_id)} disconnected.")
                                await self.remove_model(model_id)
                        except asyncio.TimeoutError:
                            # No data available yet, continue to next model
                            continue
                        except Exception as e:
                            print(f"\nError receiving from model {model_id}: {e}")
                
                # Small delay to prevent CPU hogging
                await asyncio.sleep(0.1)
                
        except asyncio.CancelledError:
            print("\nReceiver task cancelled.")
        except Exception as e:
            print(f"\nError in receiver loop: {e}")
        
    async def handle_model_response(self, model_id, data):
        """
        Handle and display a response from an AI model.
        
        Args:
            model_id (str): Identifier for the model that sent the response
            response (str): The response content
        """
        try:
            # Decode response
            response_text = data.decode('utf-8').strip()
            
            # Try to parse as JSON
            try:
                response = json.loads(response_text)
                
                # Check message type
                msg_type = response.get("message_type", "")
                
                if msg_type == "generation_result":
                    # Display generated text
                    text = response.get("generated_text", "")
                    print(f"\n{text}\n")
                    
                elif msg_type == "error":
                    # Display error
                    error = response.get("error", "Unknown error")
                    print(f"\nError from model: {error}\n")
                    
                elif msg_type == "capabilities":
                    # Model advertised its capabilities
                    print(f"\nModel {model_id} capabilities received.\n")
                    
                else:
                    # Unknown message type, just print the raw JSON
                    print(f"\nResponse from {model_id}: {response_text}\n")
                    
            except json.JSONDecodeError:
                # Not JSON, just print the text
                print(f"\n{response_text}\n")
                
        except Exception as e:
            print(f"\nError handling response: {e}")
        
    async def add_model(self, model_id, reader, writer):
        """
        Add a new AI model connection.
        
        Args:
            model_id (str): Identifier for the model
            reader (StreamReader): For receiving data from this model
            writer (StreamWriter): For sending data to this model
        """
        self.connected_models[model_id] = {
            "reader": reader,
            "writer": writer,
            "name": f"Model {model_id}",
            "active": False
        }
        
        print(f"\nNew model connected: {model_id}")
        
        # If this is the first model, make it active
        if not self.active_model:
            self.active_model = model_id
            self.connected_models[model_id]["active"] = True
            print(f"Model {model_id} is now active.")
        
    async def remove_model(self, model_id):
        """
        Remove an AI model connection.
        
        Args:
            model_id (str): Identifier for the model to remove
        """
        if model_id in self.connected_models:
            # Close writer if possible
            try:
                writer = self.connected_models[model_id]["writer"]
                if not writer.is_closing():
                    writer.close()
                    await writer.wait_closed()
            except Exception as e:
                print(f"Error closing connection to model {model_id}: {e}")
            
            # Remove from dictionary
            del self.connected_models[model_id]
            
            # If this was the active model, select a new one if available
            if model_id == self.active_model:
                if self.connected_models:
                    self.active_model = next(iter(self.connected_models))
                    print(f"Switched to model {self.active_model}")
                else:
                    self.active_model = None
                    print("No more models connected.")
        
    async def run(self):
        """
        Main execution loop for the CLI interface.
        Manages input handling and response receiving concurrently.
        """
        # Display welcome message
        await self.display_welcome()
        
        try:
            # Create tasks for input handling and receiving from models
            input_task = asyncio.create_task(self.handle_input())
            receive_task = asyncio.create_task(self.receive_from_model())
            
            # Store tasks for cleanup
            self.tasks.add(input_task)
            self.tasks.add(receive_task)
            
            # Wait for tasks to complete
            await asyncio.gather(input_task, receive_task)
            
        except asyncio.CancelledError:
            print("\nInterface execution cancelled.")
        except Exception as e:
            print(f"\nError in interface execution: {e}")
        finally:
            # Cancel any remaining tasks
            for task in self.tasks:
                if not task.done():
                    task.cancel()
            
            # Clean up resources
            for model_id, model_info in list(self.connected_models.items()):
                writer = model_info["writer"]
                if writer and not writer.is_closing():
                    writer.close()
            
            print("\nInterface shutdown complete.")
