import asyncio
import socket
import logging

from models.gpt2.gpt2_model import GPT2Model
from interfaces.cli_chat_interface import Cli_Chat

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("module_cont_special")

async def main():
    logger.info("Starting module_cont_special main (based on REAL code).")

    cli_interface = Cli_Chat(prompt_symbol="> ")
    gpt2_model = GPT2Model()

    # Create a socketpair for cross-wiring streams
    sock_a, sock_b = socket.socketpair()
    logger.debug(f"Socketpair created: {sock_a.fileno()}, {sock_b.fileno()}")

    # Create asyncio streams for both sides
    interface_reader, interface_writer = await asyncio.open_connection(sock=sock_a)
    model_reader, model_writer = await asyncio.open_connection(sock=sock=b)
    logger.debug("Asyncio streams created.")

    # Set up streams using the real Cli_Chat setup_streams, which manages .reader, .writer, and connected_models
    await cli_interface.setup_streams(model_reader, model_writer)
    logger.debug("cli_interface.setup_streams called.")

    # Set GPT2Model's .reader and .writer directly, as used in your actual code
    gpt2_model.reader = interface_reader
    gpt2_model.writer = interface_writer
    logger.debug("gpt2_model.reader and .writer assigned.")

    # Start model and interface run loops
    model_task = asyncio.create_task(gpt2_model.run())
    interface_task = asyncio.create_task(cli_interface.run())
    logger.info("Both run tasks started. Awaiting completion.")

    await asyncio.gather(model_task, interface_task)

    logger.info("Main event loop finished. Cleaning up.")
    interface_writer.close()
    model_writer.close()
    await interface_writer.wait_closed()
    await model_writer.wait_closed()
    logger.info("Writers closed.")

if __name__ == "__main__":
    asyncio.run(main())
