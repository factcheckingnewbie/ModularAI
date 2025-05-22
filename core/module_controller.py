#!/usr/bin/env python3
"""
Mediator between module and interface.

Features:
- Issues non-blocking calls
- Bridges connection based on compatibility checks
- No hardcoded dependency on either module or interface
"""

import asyncio
import json
import logging
import socket
from asyncio import StreamReader, StreamWriter, CancelledError
from typing import Dict, Any, Optional, Tuple, Set

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)


class ModuleController:
    """
    Mediator class  between
    interface modules and AI model modules.
    """
    
    # Protocol version for compatibility checking
    PROTOCOL_VERSION = "1.0.0"
    
    def __init__(self):
        self.interface = None
        self.model = None
        self.interface_reader = None
        self.interface_writer = None
        self.model_reader = None
        self.model_writer = None
        self.running = False
        self.tasks = set()
    
    async def connect_interface(self, interface) -> bool:
        """
        Establish a connection with the interface module.
        
        Args:
            interface: The interface module to connect to
            
        Returns:
            bool: True if connection was successful, False otherwise
        """
        try:
            self.interface = interface
            logger.info(f"Connecting to interface: {interface.__class__.__name__}")
            return True
        except Exception as e:
            logger.error(f"Error connecting to interface: {e}", exc_info=True)
            return False
    
    async def connect_model(self, model) -> bool:
        """
        Args:
            model: The model module to connect to
        Returns:
            bool: True if connection was successful, False otherwise
        """
        try:
            self.model = model
            logger.info(f"Connecting to model: {model.__class__.__name__}")
            
            # Check compatibility
            if hasattr(model, 'verify_controller_compatibility'):
                is_compatible, message = await model.verify_controller_compatibility(self.PROTOCOL_VERSION)
                if not is_compatible:
                    logger.error(f"Incompatible model: {message}")
                    return False
                logger.info(f"Model compatibility: {message}")
                
            return True
        except Exception as e:
            logger.error(f"Error connecting to model: {e}", exc_info=True)
            return False
    
    async def establish_streams(self) -> bool:
        """
        Establish StreamReader and StreamWriter pairs for both interface and model.
        Uses socket pairs for bidirectional communication.
        
        Returns:
            bool: True if streams were established successfully, False otherwise
        """
        try:
            logger.info("Establishing communication streams")
            
            # Create socket pairs for bidirectional communication
            sock1, sock2 = socket.socketpair()
            
            # Create asyncio streams from sockets
            self.model_reader, self.interface_writer = await asyncio.open_connection(sock=sock1)
            self.interface_reader, self.model_writer = await asyncio.open_connection(sock=sock2)
            
            # Set streams for model
            if hasattr(self.model, 'set_streams'):
                self.model.set_streams(self.model_reader, self.model_writer)
            else:
                logger.error("Model does not implement set_streams method")
                return False
            
            logger.info("Communication streams established successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error establishing streams: {e}", exc_info=True)
            return False
    
    async def check_compatibility(self) -> Tuple[bool, str]:
        """
        Check compatibility between interface and model.
        
        Returns:
            Tuple[bool, str]: (is_compatible, message)
                is_compatible: True if compatible, False if not
                message: Description of compatibility status
        """
        try:
            if not self.interface or not self.model:
                return False, "Interface or model not connected"
                
            # Get interface capabilities
            interface_capabilities = {}
            if hasattr(self.interface, 'get_capabilities'):
                interface_capabilities = await self.interface.get_capabilities()
                
            # Check model compatibility
            if hasattr(self.model, 'check_compatibility'):
                is_compatible, message = await self.model.check_compatibility(interface_capabilities)
                return is_compatible, message
                
            # Default compatibility (no checking)
            return True, "No compatibility checking available"
            
        except Exception as e:
            logger.error(f"Error checking compatibility: {e}", exc_info=True)
            return False, f"Error during compatibility check: {str(e)}"
    
    def _handle_task_exception(self, task):
        """Handle exceptions from completed tasks."""
        if task.cancelled():
            return
        
        exception = task.exception()
        if exception:
            logger.error(f"Task raised exception: {exception}", exc_info=exception)
            # Trigger shutdown if serious error
            self.running = False
    
    async def relay_to_model(self) -> None:
        """
        Continuously relay messages from interface to model.
        Non-blocking implementation using asyncio.
        """
        try:
#            logger.info("Starting relay from interface to model")
            logger.debug(
                "Starting relay from interface to model | running=%s interface_reader.at_eof=%s model_writer.is_closing=%s",
                self.running,
                self.interface_reader.at_eof() if self.interface_reader else None,
                self.model_writer.is_closing()    if self.model_writer    else None,
            )            
            while self.running and not self.interface_reader.at_eof():
                try:
                    # Read a line from interface
                    data = await self.interface_reader.readline()
                    if not data:
                        logger.info("Interface EOF received")
                        self.running = False  # Signal other tasks to terminate
                        # Signal EOF to the other end
                        if not self.model_writer.is_closing():
                            self.model_writer.close()
                        break
                        
                    # Parse and validate message format
                    try:
                        message = json.loads(data.decode('utf-8'))
                        # Add controller metadata
                        if isinstance(message, dict):
                            message["_controller_version"] = self.PROTOCOL_VERSION
                            data = (json.dumps(message) + '\n').encode('utf-8')
                    except json.JSONDecodeError:
                        # Not JSON, pass through unchanged
                        pass
                    
                    # Write to model
                    if not self.model_writer.is_closing():
                        self.model_writer.write(data)
                        await self.model_writer.drain()
                    else:
                        logger.warning("Model writer closed, can't send data")
                        break
                    
                except asyncio.CancelledError:
                    logger.info("Interface relay task cancelled")
                    break
                except Exception as e:
                    logger.error(f"Error relaying to model: {e}", exc_info=True)
                    # Try to continue if possible
                    await asyncio.sleep(0.1)
                    
        except Exception as e:
            logger.error(f"Fatal error in interface relay: {e}", exc_info=True)
        finally:
            logger.info("Interface to model relay ended")
    
    async def relay_to_interface(self) -> None:
        """
        Continuously relay messages from model to interface.
        Non-blocking implementation using asyncio.
        """
        try:
            logger.info("Starting relay from model to interface")
            
            while self.running and not self.model_reader.at_eof():
                try:
                    # Read a line from model
                    data = await self.model_reader.readline()
                    if not data:
                        logger.info("Model EOF received")
                        self.running = False  # Signal other tasks to terminate
                        # Signal EOF to the other end
                        if not self.interface_writer.is_closing():
                            self.interface_writer.close()
                        break
                        
                    # Parse and handle controller messages
                    try:
                        message = json.loads(data.decode('utf-8'))
                        
                        # Check for controller notifications
                        if isinstance(message, dict) and message.get("message_type") == "controller_notification":
                            await self.handle_controller_notification(message)
                            # Skip forwarding to interface if it's controller-specific
                            if message.get("notification_type") in ["controller_only"]:
                                continue
                    except json.JSONDecodeError:
                        # Not JSON, pass through
                        pass
                    
                    # Write to interface
                    if not self.interface_writer.is_closing():
                        self.interface_writer.write(data)
                        await self.interface_writer.drain()
                    else:
                        logger.warning("Interface writer closed, can't send data")
                        break
                    
                except asyncio.CancelledError:
                    logger.info("Model relay task cancelled")
                    break
                except Exception as e:
                    logger.error(f"Error relaying to interface: {e}", exc_info=True)
                    # Try to continue if possible
                    await asyncio.sleep(0.1)
                    
        except Exception as e:
            logger.error(f"Fatal error in model relay: {e}", exc_info=True)
        finally:
            logger.info("Model to interface relay ended")
    
    async def handle_controller_notification(self, notification: Dict[str, Any]) -> None:
        """
        Handle notifications directed to the controller.
        
        Args:
            notification: The notification message
        """
        notification_type = notification.get("notification_type")
        
        if notification_type == "critical_error":
            error = notification.get("error", "Unknown critical error")
            logger.critical(f"Critical error notification from model: {error}")
            # Initiate shutdown
            asyncio.create_task(self.close())
        elif notification_type == "status":
            status = notification.get("status", "Unknown status")
            logger.info(f"Status notification from model: {status}")
        else:
            logger.debug(f"Unknown notification type: {notification_type}")
    
    async def start_mediation(self) -> bool:
        """
        Start the bidirectional communication between interface and model.
        Creates and manages non-blocking tasks for communication.
        
        Returns:
            bool: True if started successfully, False otherwise
        """
        if not self.interface or not self.model:
            logger.error("Cannot start mediation: Interface or model not connected")
            return False
            
        if not self.interface_reader or not self.interface_writer or \
           not self.model_reader or not self.model_writer:
            logger.error("Cannot start mediation: Streams not established")
            return False
            
        # Check compatibility
        is_compatible, message = await self.check_compatibility()
        if not is_compatible:
            logger.error(f"Incompatible modules: {message}")
            return False
            
        logger.info(f"Compatibility check passed: {message}")
        
        try:
            self.running = True
            
            # Create relay tasks
            interface_relay_task = asyncio.create_task(self.relay_to_model())
            model_relay_task = asyncio.create_task(self.relay_to_interface())
            
            # Store tasks for cleanup
            self.tasks.add(interface_relay_task)
            self.tasks.add(model_relay_task)
            
            # Add exception handlers
            interface_relay_task.add_done_callback(
                lambda t: self._handle_task_exception(t) if not t.cancelled() else None)
            model_relay_task.add_done_callback(
                lambda t: self._handle_task_exception(t) if not t.cancelled() else None)
            
            # Remove tasks when they complete
            interface_relay_task.add_done_callback(self.tasks.discard)
            model_relay_task.add_done_callback(self.tasks.discard)
            
            logger.info("Mediation started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error starting mediation: {e}", exc_info=True)
            self.running = False
            return False
    
    async def close(self) -> None:
        """
        Close all connections and clean up resources.
        """
        logger.info("Shutting down module controller")
        self.running = False
        
        # Cancel all tasks
        for task in self.tasks:
            if not task.done():
                task.cancel()
                
        # Wait for tasks to complete with reasonable timeout
        if self.tasks:
            try:
                await asyncio.wait(
                    self.tasks, 
                    timeout=2.0,
                    return_when=asyncio.ALL_COMPLETED
                )
            except Exception as e:
                logger.error(f"Error waiting for tasks: {e}", exc_info=True)
        
        # Close writers
        if self.model_writer and not self.model_writer.is_closing():
            try:
                self.model_writer.close()
                await asyncio.sleep(0.1)  # Brief pause to allow closure
            except Exception as e:
                logger.error(f"Error closing model writer: {e}", exc_info=True)
                
        if self.interface_writer and not self.interface_writer.is_closing():
            try:
                self.interface_writer.close()
                await asyncio.sleep(0.1)  # Brief pause to allow closure
            except Exception as e:
                logger.error(f"Error closing interface writer: {e}", exc_info=True)
        
        # Close model if it has a close method
        if hasattr(self.model, 'close'):
            try:
                await self.model.close()
            except Exception as e:
                logger.error(f"Error closing model: {e}", exc_info=True)
        
        # Clear references
        self.interface = None
        self.model = None
        self.interface_reader = None
        self.interface_writer = None
        self.model_reader = None
        self.model_writer = None
        self.tasks.clear()
        logger.info("Module controller shutdown complete")
