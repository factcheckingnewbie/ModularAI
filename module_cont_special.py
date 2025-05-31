import logging
import asyncio

# Set up logging for debugging (prints to stdout)
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("module_cont_special")

class ModuleContSpecial:
    def __init__(self):
        self.interface = None
        self.model = None
        self.connected = False
        logger.info("Special controller initialized (no modules connected).")

    def add_interface(self, interface):
        if self.interface is not None:
            raise RuntimeError("Interface already attached!")
        self.interface = interface
        logger.info(f"Interface module added: {interface.__class__.__name__} (id={id(interface)})")

    def add_model(self, model):
        if self.model is not None:
            raise RuntimeError("Model already attached!")
        self.model = model
        logger.info(f"Model module added: {model.__class__.__name__} (id={id(model)})")

    def connect_modules(self):
        if self.interface is None or self.model is None:
            raise RuntimeError("Both interface and model must be attached before connecting!")
        # Create a socket pair for cross-wiring streams
        import socket
        sock_a, sock_b = socket.socketpair()
        # Side A for interface, Side B for model
        # Attach asyncio streams
        async def setup_streams():
            interface_reader, interface_writer = await asyncio.open_connection(sock=sock_a)
            model_reader, model_writer = await asyncio.open_connection(sock=sock_b)
            # Cross-wire: interface <-> model
            self.interface.reader = model_reader
            self.interface.writer = model_writer
            self.model.reader = interface_reader
            self.model.writer = interface_writer
            logger.info("Streams cross-wired: interface.reader=model_reader, model.reader=interface_reader")
        self._setup_streams_coro = setup_streams
        self.connected = True
        logger.info(f"Modules connected: interface={self.interface.__class__.__name__}, model={self.model.__class__.__name__}")

    async def run(self):
        if not self.connected:
            logger.warning("Cannot run: Modules not connected!")
            return
        # Actually set up the streams
        await self._setup_streams_coro()
        logger.info("Streams setup complete.")
        # Optionally: run interface and model in background (if they have async run loops)
        tasks = []
        if hasattr(self.model, "run") and asyncio.iscoroutinefunction(self.model.run):
            tasks.append(asyncio.create_task(self.model.run()))
            logger.info(f"Started async model.run() for {self.model.__class__.__name__}")
        if hasattr(self.interface, "run") and asyncio.iscoroutinefunction(self.interface.run):
            tasks.append(asyncio.create_task(self.interface.run()))
            logger.info(f"Started async interface.run() for {self.interface.__class__.__name__}")
        if tasks:
            await asyncio.gather(*tasks)
        else:
            logger.warning("Neither module has an async run() method; nothing to run.")
        logger.info("Controller run loop finished.")

# ---- Your Model Module Block ----
from models.gpt2.gpt2_model import GPT2Model

# ---- Your Interface Module Block ----
from interfaces.cli_chat_interface import Cli_Chat

# ---- Main Entrypoint ----
if __name__ == "__main__":
    logger.info("Starting module_cont_special main.")
    controller = ModuleContSpecial()
    # Add your interface module
    cli_interface = Cli_Chat(prompt_symbol="> ")
    logger.debug(f"Instantiated Cli_Chat: {cli_interface.__class__.__name__} (id={id(cli_interface)})")
    controller.add_interface(cli_interface)
    # Add your model module
    gpt2_model = GPT2Model()
    logger.debug(f"Instantiated GPT2Model: {gpt2_model.__class__.__name__} (id={id(gpt2_model)})")
    controller.add_model(gpt2_model)
    # Connect them
    controller.connect_modules()
    # Run everything
    asyncio.run(controller.run())
