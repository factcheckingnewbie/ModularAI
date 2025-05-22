#!/usr/bin/env python3
"""
GPT-2 based AI model for the ModdularAI framework.

Features:
- Provides AI functionalities
- Operates in a non-blocking manner
- No built-in knowledge of the interface; relies on external connection mediation
- Explicit compatibility checking
- Proper resource management
- Robust error handling and cancellation support
"""

import asyncio
import json
import logging
from asyncio import StreamReader, StreamWriter, CancelledError, TimeoutError
from typing import Dict, Any, Optional, Tuple

# We'll import transformers modules dynamically to avoid hard dependency

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GPT2Model:
    """
    GPT-2 based AI model that operates in a non-blocking manner using asyncio streams.
    
    The model handles communication through standard stream interfaces and 
    implements proper compatibility checking and resource management.
    """
    
    # Protocol version for compatibility checking
    PROTOCOL_VERSION = "1.0.0"
    
    # Model capabilities for compatibility checking
    CAPABILITIES = {
        "text_io": True,
        "structured_output": False,
        "language_understanding": True
    }
    
    def __init__(self):
        """Initialize the GPT-2 model."""
        self.reader: Optional[StreamReader] = None
        self.writer: Optional[StreamWriter] = None
        self.generator = None
        self.running = False
        self.tasks = set()
        self.config = {
            "max_response_tokens": 1000,
            "temperature": 0.7,
            "request_timeout": 30,  # Timeout for requests in seconds
        }
    def get_model_id(self) -> str:
        """
        Return the model ID used in config/model_modules.json.
        """
        return "gpt2"
    async def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """
        Initialize the model with configuration parameters.
        
        Args:
            config: Dictionary of configuration parameters
            
        Returns:
            bool: True if initialization was successful, False otherwise
        """
        if config:
            self.config.update(config)
            
        # Load the model asynchronously
        return await self.load_model()
    
    async def load_model(self) -> bool:
        """
        Load the GPT-2 model in a non-blocking manner.
        
        Returns:
            bool: True if the model was loaded successfully, False otherwise
        """
        logger.info("Loading GPT-2 model...")
        try:
            # Dynamically import transformers to avoid hard dependency
            # This allows the module to be loaded even if transformers is not installed
            # The actual error will only occur when trying to use the model
            try:
                from transformers import pipeline, AutoTokenizer
            except ImportError:
                logger.error("Transformers library not found. Please install it with 'pip install transformers'")
                return False
                
            # Use run_in_executor to avoid blocking the event loop
            loop = asyncio.get_running_loop()
            
            # Initialize tokenizer with proper pad_token to avoid warnings
            tokenizer = await loop.run_in_executor(
                None,
                lambda: self._initialize_tokenizer('gpt2')
            )
            
            # Create pipeline with configured tokenizer
            self.generator = await loop.run_in_executor(
                None, 
                lambda: pipeline('text-generation', model='gpt2', tokenizer=tokenizer)
            )
            logger.info("Model loaded successfully")
            return True
        except Exception as e:
            logger.error(f"Error loading model: {e}", exc_info=True)
            self.generator = None
            return False
    
    def set_streams(self, reader: StreamReader, writer: StreamWriter) -> None:
        """
        Set the StreamReader and StreamWriter for communication.
        
        Args:
            reader: StreamReader instance for receiving data
            writer: StreamWriter instance for sending data
        """
        self.reader = reader
        self.writer = writer
    
    async def verify_controller_compatibility(self, controller_version: str) -> Tuple[bool, str]:
        """
        Check compatibility with the module controller.
        
        Args:
            controller_version: Version string of the module controller
            
        Returns:
            Tuple[bool, str]: (is_compatible, message)
        """
        # Simple version check for now
        if controller_version >= "1.0.0":
            return True, "Compatible with controller"
        return False, f"Incompatible controller version: {controller_version}, requires >= 1.0.0"
    
    async def check_compatibility(self, interface_capabilities: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Check compatibility with an interface based on its capabilities.
        
        Args:
            interface_capabilities: Dictionary of capabilities required by the interface
            
        Returns:
            Tuple[bool, str]: (is_compatible, message)
                is_compatible: True if fully compatible, False if not
                message: Description of compatibility status
        """
        if not interface_capabilities:
            return True, "No capability requirements specified"
            
        # Check required capabilities
        if "required_capabilities" in interface_capabilities:
            for capability in interface_capabilities["required_capabilities"]:
                if capability not in self.CAPABILITIES or not self.CAPABILITIES[capability]:
                    return False, f"Required capability '{capability}' not supported"
        
        # Check optional capabilities (these don't affect compatibility status)
        missing_optional = []
        if "optional_capabilities" in interface_capabilities:
            for capability in interface_capabilities["optional_capabilities"]:
                if capability not in self.CAPABILITIES or not self.CAPABILITIES[capability]:
                    missing_optional.append(capability)
        
        if missing_optional:
            return True, f"Compatible, but missing optional capabilities: {', '.join(missing_optional)}"
        
        return True, "Fully compatible"
    
    async def advertise_capabilities(self) -> None:
        """
        Send model capabilities to the connected interface.
        """
        if not self.writer:
            logger.error("Cannot advertise capabilities: Writer not set")
            return
            
        try:
            capability_info = {
                "message_type": "capabilities",
                "protocol_version": self.PROTOCOL_VERSION,
                "capabilities": self.CAPABILITIES
            }
            
            # Send capabilities as JSON
            capability_json = json.dumps(capability_info) + '\n'
            self.writer.write(capability_json.encode('utf-8'))
            await self.writer.drain()
            
            logger.info("Sent capability information")
        except Exception as e:
            logger.error(f"Error advertising capabilities: {e}", exc_info=True)
    
    async def run(self) -> bool:
        """
        Run the model processing loop, handling incoming requests.
        
        This is the main entry point after connecting streams.
        
        Returns:
            bool: True if exited normally, False if error occurred
        """
        if not self.reader or not self.writer:
            logger.error("Error: Streams not set")
            return False
        
        # Set running flag    
        self.running = True
            
        try:
            # First, advertise capabilities
            await self.advertise_capabilities()
            
            # Process incoming messages
            while self.running and not self.reader.at_eof():
                try:
                    # Read a line with timeout
                    try:
                        # Use wait_for to implement timeout
                        data = await asyncio.wait_for(
                            self.reader.readline(),
                            timeout=self.config.get("request_timeout", 30)
                        )
                    except TimeoutError:
                        # No data received within timeout, but connection still alive
                        continue
                    
                    if not data:
                        # EOF reached
                        logger.info("End of stream reached")
                        break
                        
                    # Process request in a separate task to avoid blocking the main loop
                    task = asyncio.create_task(self.process_request(data))
                    self.tasks.add(task)
                    task.add_done_callback(self.tasks.discard)
                    
                except CancelledError:
                    # Handle cancellation
                    logger.info("Model processing loop cancelled")
                    break
                except Exception as e:
                    logger.error(f"Error in model run loop: {e}", exc_info=True)
                    # Continue processing other requests
                    continue
                    
            return True
            
        except Exception as e:
            logger.error(f"Fatal error in run loop: {e}", exc_info=True)
            return False
        finally:
            self.running = False
            # Cancel all pending tasks
            for task in self.tasks:
                if not task.done():
                    task.cancel()
            
            # Wait for tasks to complete
            if self.tasks:
                try:
                    await asyncio.gather(*self.tasks, return_exceptions=True)
                except Exception as e:
                    logger.error(f"Error waiting for tasks to complete: {e}", exc_info=True)
            
            logger.info("Model processing loop ended")
    
    async def process_request(self, data: bytes) -> None:
        """
        Process an incoming request.
        
        Args:
            data: Raw bytes of the request
        """
        try:
            # Decode and parse JSON
            message = data.decode('utf-8').strip()
            if not message:
                return
                
            # Parse JSON and validate format
            try:
                request = json.loads(message)
            except json.JSONDecodeError:
                logger.error(f"Received invalid JSON: {message}")
                await self.handle_error("Invalid JSON format")
                return
            
            # Validate message type
            message_type = request.get("message_type", "text_generation")
            
            # Handle different message types
            if message_type == "text_generation":
                await self.handle_text_generation(request)
            elif message_type == "compatibility_check":
                await self.handle_compatibility_check(request)
            elif message_type == "ping":
                await self.handle_ping(request)
            elif message_type == "shutdown":
                await self.handle_shutdown(request)
            else:
                logger.warning(f"Unknown message type: {message_type}")
                await self.handle_error(f"Unknown message type: {message_type}", request.get("request_id"))
                
        except CancelledError:
            # Properly handle task cancellation
            logger.info("Request processing cancelled")
            raise
        except Exception as e:
            logger.error(f"Error processing request: {e}", exc_info=True)
            await self.handle_error(f"Internal error: {str(e)}")
    
    async def handle_text_generation(self, request: Dict[str, Any]) -> None:
        """
        Handle a text generation request.
        
        Args:
            request: The parsed request object
        """
        if "prompt" not in request:
            await self.handle_error("Missing 'prompt' field", request.get("request_id"))
            return
            
        prompt = request["prompt"]
        request_id = request.get("request_id")
        
        logger.info(f"Generating text for request ID: {request_id}")
        
        # Generate text
        try:
            generated_text = await self.generate_text(
                prompt, 
                max_length=request.get("max_length", self.config.get("max_response_tokens")),
                temperature=request.get("temperature", self.config.get("temperature"))
            )
            
            # Build response
            response = {
                "message_type": "generation_result",
                "original_prompt": prompt,
                "generated_text": generated_text,
                "status": "success"
            }
            
            if request_id:
                response["request_id"] = request_id
            
            # Send response
            await self.send_response(response)
            
        except Exception as e:
            logger.error(f"Error generating text: {e}", exc_info=True)
            await self.handle_error(f"Error generating text: {str(e)}", request_id)
    
    async def handle_compatibility_check(self, request: Dict[str, Any]) -> None:
        """
        Handle a compatibility check request.
        
        Args:
            request: The parsed request object
        """
        capabilities = request.get("capabilities", {})
        request_id = request.get("request_id")
        
        is_compatible, message = await self.check_compatibility(capabilities)
        
        response = {
            "message_type": "compatibility_result",
            "compatible": is_compatible,
            "message": message,
            "protocol_version": self.PROTOCOL_VERSION,
            "capabilities": self.CAPABILITIES
        }
        
        if request_id:
            response["request_id"] = request_id
            
        await self.send_response(response)
    
    async def handle_ping(self, request: Dict[str, Any]) -> None:
        """
        Handle a ping request.
        
        Args:
            request: The parsed request object
        """
        request_id = request.get("request_id")
        
        response = {
            "message_type": "pong",
            "status": "alive"
        }
        
        if request_id:
            response["request_id"] = request_id
            
        await self.send_response(response)
    
    async def handle_shutdown(self, request: Dict[str, Any]) -> None:
        """
        Handle a shutdown request.
        
        Args:
            request: The parsed request object
        """
        request_id = request.get("request_id")
        
        response = {
            "message_type": "shutdown_ack",
            "status": "shutting_down"
        }
        
        if request_id:
            response["request_id"] = request_id
            
        await self.send_response(response)
        
        # Schedule shutdown
        asyncio.create_task(self.shutdown())
    
    async def handle_error(self, error_message: str, request_id: Optional[str] = None, 
                           source: str = "model", is_critical: bool = False) -> None:
        """
        Handle and report an error.
        
        Args:
            error_message: The error message
            request_id: Optional request ID to include in the response
            source: Source of the error (model, controller, etc.)
            is_critical: Whether this is a critical error requiring shutdown
        """
        error_response = {
            "message_type": "error",
            "error": error_message,
            "source": source,
            "is_critical": is_critical,
            "status": "error"
        }
        
        if request_id:
            error_response["request_id"] = request_id
            
        await self.send_response(error_response)
        
        # If critical error, initiate shutdown
        if is_critical:
            logger.critical(f"Critical error: {error_message}")
            await self.notify_controller_error(error_message)
            asyncio.create_task(self.shutdown())
    
    async def notify_controller_error(self, error_message: str) -> None:
        """
        Notify the controller about a critical error.
        
        Args:
            error_message: The error message to send
        """
        notification = {
            "message_type": "controller_notification",
            "notification_type": "critical_error",
            "error": error_message
        }
        
        await self.send_response(notification)
    
    async def generate_text(self, prompt: str, max_length: Optional[int] = None, 
                           temperature: Optional[float] = None) -> str:
        """
        Generate text based on the given prompt.
        
        Args:
            prompt: The input prompt
            max_length: Maximum length of generated text
            temperature: Temperature for generation
            
        Returns:
            The generated text as a string
        """
        # Ensure model is loaded
        if not self.generator:
            if not await self.load_model():
                return f"Error: Model not loaded. Received prompt: {prompt}"
        
        # Use provided or default parameters
        max_length = max_length or self.config.get('max_response_tokens', 250)
        temperature = temperature or self.config.get('temperature', 0.7)
        
        # Run in executor to avoid blocking
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None,
            lambda: self.generator(
                prompt,
                max_length=max_length,
                truncation=True,
                do_sample=True,
                temperature=temperature,
                top_k=50,
                top_p=0.92,
                num_return_sequences=1
            )
        )
        
        generated_text = result[0]['generated_text']
        
        # Post-processing for complete sentences
        sentence_endings = ['.', '!', '?']
        last_end_pos = max([generated_text.rfind(ending) for ending in sentence_endings])
        
        if last_end_pos > 0 and last_end_pos < len(generated_text) - 1:
            return generated_text[:last_end_pos + 1]
        return generated_text
    
    async def send_response(self, response: Dict[str, Any]) -> None:
        """
        Send a response back through the writer stream.
        
        Args:
            response: Dictionary containing the response data
        """
        if not self.writer:
            logger.error("Error: Writer not set")
            return
            
        try:
            # Convert to JSON and add newline
            response_json = json.dumps(response) + '\n'
            
            # Write and flush
            self.writer.write(response_json.encode('utf-8'))
            await self.writer.drain()
            
            logger.debug(f"Response sent: {response.get('message_type', 'unknown')}")
        except ConnectionError as e:
            logger.error(f"Connection error sending response: {e}")
        except Exception as e:
            logger.error(f"Error sending response: {e}", exc_info=True)
    
    def _initialize_tokenizer(self, model_name: str):
        """
        Initialize a tokenizer with proper pad_token configuration.
        
        Args:
            model_name: Name of the model to load tokenizer for
            
        Returns:
            Configured tokenizer
        """
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        # GPT-2 doesn't have a pad token by default, set it to the EOS token
        # This avoids warnings about setting pad_token_id to eos_token_id
        tokenizer.pad_token = tokenizer.eos_token
        return tokenizer
        
    async def shutdown(self) -> None:
        """Shutdown the model gracefully."""
        logger.info("Shutting down model")
        self.running = False
        
        # Cancel all pending tasks
        for task in self.tasks:
            if not task.done():
                task.cancel()
                
        # Close connection
        await self.close()
    
    async def close(self) -> None:
        """Close the connection and clean up resources."""
        if self.writer:
            try:
                self.writer.close()
                await self.writer.wait_closed()
            except Exception as e:
                logger.error(f"Error closing writer: {e}", exc_info=True)
        
        # Clean up resources
        self.reader = None
        self.writer = None
        self.generator = None  # Release the model
        
        logger.info("Model connection closed and resources released")
