#!/usr/bin/env python3
"""
Main loop: Reads configuration files, presents menus, connects interface and AI-model.
"""
import asyncio
import json
import importlib
import inspect
import os
import sys
from pathlib import Path


class ModuleManager:
    """
    Main module manager class responsible for reading configs, presenting menus,
    and connecting interfaces with AI models.
    """
    
    def __init__(self):
        """Initialize the ModuleManager."""
        self.interfaces = {}
        self.models = {}
        self.controller = None
        
    async def load_config_files(self):
        """
        Load configuration files for interfaces and models.
        
        Reads:
        - ./config/interface_modules.json
        - ./config/model_modules.json
        
        Returns:
            bool: True if configs loaded successfully, False otherwise
        """
        # Check file paths existence before access attempts
        interface_path = Path('./config/interface_modules.json')
        model_path = Path('./config/model_modules.json')
        
        if not interface_path.exists():
            print(f"Error: Interface configuration file not found at {interface_path}")
            return False
            
        if not model_path.exists():
            print(f"Error: Model configuration file not found at {model_path}")
            return False
        
        try:
            # Load interfaces configuration
            with open(interface_path, 'r') as f:
                interface_data = json.load(f)
                self.interfaces = interface_data.get('interfaces', [])
                
            # Load models configuration
            with open(model_path, 'r') as f:
                model_data = json.load(f)
                self.models = model_data.get('models', [])
                
            # Validate configurations
            if not self.interfaces:
                print("Error: No interfaces found in configuration.")
                return False
                
            if not self.models:
                print("Error: No models found in configuration.")
                return False
                
            print(f"Loaded {len(self.interfaces)} interfaces and {len(self.models)} models")
            return True
            
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in configuration file: {e}")
            return False
        except Exception as e:
            print(f"Error loading configuration files: {e}")
            return False
        
    async def present_interface_menu(self):
        """
        Present menu for the user to select an interface.
        
        Returns:
            dict: Selected interface configuration or None if selection failed
        """
        print("\nAvailable Interfaces:")
        print("---------------------")
        
        for i, interface in enumerate(self.interfaces, 1):
            print(f"{i}. {interface['name']} - {interface['description']}")
        
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                choice = int(input("\nSelect an interface (number): "))
                if 1 <= choice <= len(self.interfaces):
                    return self.interfaces[choice-1]
                else:
                    print(f"Invalid choice. Please enter a number between 1 and {len(self.interfaces)}")
            except ValueError:
                print("Please enter a valid number.")
            except Exception as e:
                print(f"Error: {e}")
        
        print("Maximum number of attempts reached. Interface selection failed.")
        return None
        
    async def present_model_menu(self):
        """
        Present menu for the user to select an AI model.
        
        Returns:
            dict: Selected model configuration or None if selection failed
        """
        print("\nAvailable AI Models:")
        print("--------------------")
        
        for i, model in enumerate(self.models, 1):
            print(f"{i}. {model['name']} - {model['description']}")
        
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                choice = int(input("\nSelect a model (number): "))
                if 1 <= choice <= len(self.models):
                    return self.models[choice-1]
                else:
                    print(f"Invalid choice. Please enter a number between 1 and {len(self.models)}")
            except ValueError:
                print("Please enter a valid number.")
            except Exception as e:
                print(f"Error: {e}")
        
        print("Maximum number of attempts reached. Model selection failed.")
        return None
        
    async def check_compatibility(self, interface, model):
        """
        Check compatibility between selected interface and model.
        
        Args:
            interface (dict): Interface configuration
            model (dict): Model configuration
            
        Returns:
            str or bool: 
                - True if fully compatible
                - 'partial' if partially compatible
                - False if incompatible
        """
        # Extract compatibility requirements and capabilities
        required_capabilities = interface.get('compatibility', {}).get('required_capabilities', [])
        optional_capabilities = interface.get('compatibility', {}).get('optional_capabilities', [])
        model_capabilities = model.get('capabilities', {})
        
        # Verify data integrity
        if not isinstance(required_capabilities, list) or not isinstance(optional_capabilities, list):
            print("Error: Invalid compatibility format in interface configuration")
            return False
            
        if not isinstance(model_capabilities, dict):
            print("Error: Invalid capabilities format in model configuration")
            return False
        
        # Check required capabilities
        missing_required = []
        for capability in required_capabilities:
            if not model_capabilities.get(capability, False):
                missing_required.append(capability)
        
        if missing_required:
            print(f"Incompatible: Model missing required capabilities: {', '.join(missing_required)}")
            return False
        
        # Check optional capabilities
        missing_optional = []
        for capability in optional_capabilities:
            if not model_capabilities.get(capability, False):
                missing_optional.append(capability)
        
        # Return compatibility level
        if missing_optional:
            print(f"Partially compatible: Model missing optional capabilities: {', '.join(missing_optional)}")
            return 'partial'
        
        print("Fully compatible: All required and optional capabilities are supported")
        return True
        
    async def _import_module(self, module_path):
        """
        Helper function to dynamically import a module from a file path.
        
        Args:
            module_path (str): Path to the module
            
        Returns:
            module: Imported module or None if import failed
        """
        # Verify path exists before attempting import
        path = Path(module_path)
        if not path.exists():
            print(f"Error: Module path does not exist: {module_path}")
            return None
            
        try:
            # Convert file path to module path
            if module_path.startswith('./'):
                module_path = module_path[2:]
                
            # Replace slashes with dots and remove .py extension
            module_name = module_path.replace('/', '.').replace('.py', '')
            
            # Import the module
            module = importlib.import_module(module_name)
            return module
            
        except ImportError as e:
            print(f"Error importing module {module_path}: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error importing module {module_path}: {e}")
            return None
    
    async def _find_model_by_id(self, module, expected_id):
        """
        Find a model class in a module that reports the expected model_id.
        
        Args:
            module: Imported Python module
            expected_id (str): Model ID from configuration
            
        Returns:
            object: Instance of model class or None if not found
        """
        if not module:
            return None
            
        # Look for any class that has a get_model_id method
        for name, cls in inspect.getmembers(module, inspect.isclass):
            try:
                # Attempt to instantiate
                instance = cls()
                
                # Check if it has the get_model_id method
                if hasattr(instance, 'get_model_id'):
                    model_id = instance.get_model_id()
                    
                    # Check if ID matches
                    if model_id == expected_id:
                        print(f"Found model class {name} with matching ID: {expected_id}")
                        return instance
                        
            except Exception as e:
                # Skip classes that can't be instantiated
                continue
                
        # No matching model found
        print(f"Warning: No model found with ID '{expected_id}' in module")
        
        # Find any usable model class as fallback
        for name, cls in inspect.getmembers(module, inspect.isclass):
            try:
                instance = cls()
                print(f"Using model class {name} as fallback")
                return instance
            except Exception:
                continue
                
        print(f"Error: No usable model class found in module")
        return None
        
    async def _find_interface_by_id(self, module, expected_id):
        """
        Find an interface class in a module that reports the expected interface_id.
        
        Args:
            module: Imported Python module
            expected_id (str): Interface ID from configuration
            
        Returns:
            object: Instance of interface class or None if not found
        """
        if not module:
            return None
            
        # Look for any class that has a get_interface_id method
        for name, cls in inspect.getmembers(module, inspect.isclass):
            try:
                # Attempt to instantiate
                instance = cls()
                
                # Check if it has the get_interface_id method
                if hasattr(instance, 'get_interface_id'):
                    interface_id = instance.get_interface_id()
                    
                    # Check if ID matches
                    if interface_id == expected_id:
                        print(f"Found interface class {name} with matching ID: {expected_id}")
                        return instance
                        
            except Exception as e:
                # Skip classes that can't be instantiated
                continue
                
        # No matching interface found, try to find a usable class
        main_classes = []
        for name, cls in inspect.getmembers(module, inspect.isclass):
            if name == 'CliChatGpt':  # Known class from file inspection
                try:
                    instance = cls()
                    print(f"Using interface class {name}")
                    return instance
                except Exception as e:
                    print(f"Error instantiating {name}: {e}")
                    
        # If no specific class found, try any class
        for name, cls in inspect.getmembers(module, inspect.isclass):
            try:
                if name.startswith('_'):
                    continue
                instance = cls()
                print(f"Using interface class {name} as fallback")
                return instance
            except Exception:
                continue
                
        print(f"Error: No usable interface class found in module")
        return None
        
    async def connect_modules(self, interface_config, model_config):
        """
        Connect the selected interface and model using the module controller.
        
        Args:
            interface_config (dict): Selected interface configuration
            model_config (dict): Selected model configuration
            
        Returns:
            bool: True if connection was successful, False otherwise
        """
        # Import modules
        print(f"Importing interface module from: {interface_config['path']}")
        interface_module = await self._import_module(interface_config['path'])
        
        print(f"Importing model module from: {model_config['path']}")
        model_module = await self._import_module(model_config['path'])
        
        if not interface_module:
            print("Error: Failed to import interface module")
            return False
            
        if not model_module:
            print("Error: Failed to import model module")
            return False
        
        # Import controller module
        controller_path = './core/module_controller.py'
        print(f"Importing controller module from: {controller_path}")
        controller_module = await self._import_module(controller_path)
        
        if not controller_module:
            print("Error: Failed to import module controller")
            return False
        
        # Find and instantiate interface class
        interface_id = interface_config['id']
        interface_instance = await self._find_interface_by_id(interface_module, interface_id)
        
        if not interface_instance:
            print(f"Error: Could not find or instantiate interface with ID: {interface_id}")
            return False
        
        # Find and instantiate model class
        model_id = model_config['id']
        model_instance = await self._find_model_by_id(model_module, model_id)
        
        if not model_instance:
            print(f"Error: Could not find or instantiate model with ID: {model_id}")
            return False
        
#        # Create controller instance
#        controller_class = getattr(controller_module, 'ModuleController', None)
#        if not controller_class:
#            print("Error: ModuleController class not found in controller module")
#            return False
#            
#        controller = controller_class()
#        
#        # Connect modules through controller
#        print("Connecting interface to controller...")
#        if not await controller.connect_interface(interface_instance):
#            print("Error: Failed to connect interface to controller")
#            return False
#            
#        print("Connecting model to controller...")
#        if not await controller.connect_model(model_instance):
#            print("Error: Failed to connect model to controller")
#            return False
#            
#        print("Establishing communication streams...")
#        if not await controller.establish_streams():
#            print("Error: Failed to establish communication streams")
#            return False
#            
#        print("Starting mediation...")
#        if not await controller.start_mediation():
#            print("Error: Failed to start mediation between modules")
#            return False
#            
#        print("Successfully connected modules through controller")
#        self.controller = controller
#        return True
        
        # Instantiate and run the simplified ModuleController bridge
        controller_class = getattr(controller_module, 'ModuleController', None)
        if not controller_class:
            print("Error: ModuleController class not found in controller module")
            return False

        controller = controller_class()
        # Initialize the bridge (load model, set up streams)
        if not await controller.setup():
            print("Error: Controller setup failed")
            return False

        # Hand off control to the bridge's run loop
        await controller.run()
        self.controller = controller
        return True


    async def run(self):
        """
        Main execution loop for the ModuleManager.
        
        1. Load configurations
        2. Present interface selection menu
        3. Present model selection menu
        4. Check compatibility
        5. If models compatible, connect modules
        6. Detach and exit
        
        Returns:
            bool: True if execution was successful, False otherwise
        """
        print("\nModdularAI Module Manager")
        print("=========================")
        
        # Step 1: Load configurations
        print("\nLoading configuration files...")
        if not await self.load_config_files():
            print("Failed to load configuration files. Exiting.")
            return False
        
        # Step 2: Present interface selection menu
        selected_interface = await self.present_interface_menu()
        if not selected_interface:
            print("Interface selection failed. Exiting.")
            return False
        
        print(f"\nSelected interface: {selected_interface['name']}")
        
        # Step 3: Present model selection menu
        selected_model = await self.present_model_menu()
        if not selected_model:
            print("Model selection failed. Exiting.")
            return False
        
        print(f"\nSelected model: {selected_model['name']}")
        
        # Step 4: Check compatibility
        print("\nChecking compatibility...")
        compatibility = await self.check_compatibility(selected_interface, selected_model)
        
        if compatibility is False:
            print("Selected interface and model are incompatible. Exiting.")
            return False
        elif compatibility == 'partial':
            print("\nWarning: Partial compatibility detected.")
            
            max_attempts = 3
            for attempt in range(max_attempts):
                confirm = input("Continue anyway? (y/n): ").lower()
                if confirm == 'y':
                    break
                elif confirm == 'n':
                    print("User cancelled. Exiting.")
                    return False
                else:
                    print("Please enter 'y' or 'n'")
            else:
                print("Too many invalid attempts. Exiting.")
                return False
        
        # Step 5: Connect modules
        print("\nConnecting modules...")
        if not await self.connect_modules(selected_interface, selected_model):
            print("Failed to connect modules. Exiting.")
            return False
        
        # Step 6: Detach and exit
        print("\nModules successfully connected. Module Manager detaching...")
        print("ModuleManager job complete. Exiting.")
        
        return True


async def main():
    """Main entry point for ModdularAI."""
    try:
        manager = ModuleManager()
        result = await manager.run()
        
        if result:
            print("ModdularAI startup successful")
        else:
            print("ModdularAI startup failed")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\nModdularAI startup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error during ModdularAI startup: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
