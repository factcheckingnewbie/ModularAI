#!/usr/bin/env python3
"""
Next iteration: fix the gather logic so only one consumer
reads from interface_reader. We split into two coroutines:

  - pump_cli_to_model(): pumps raw bytes from cli.interface_reader to cli.model_writer
  - pump_model_to_cli(): pumps raw bytes from cli.model_reader to cli.interface_writer

This module acts purely as an event loop shuttling raw byte streams between
the chat CLI and the GPT-2 model, without any decoding or text processing.
"""

import os
import sys
import asyncio
import socket

# ensure project root is on PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from interfaces.cli_chat_interface import Cli_Chat
from models.gpt2.gpt2_model import GPT2Model

async def pump_cli_to_model(cli):
    """
    Read raw bytes from cli.interface_reader and write them to cli.model_writer.
    No decoding or processing of the byte stream.
    """
    try:
        while True:
            data = await cli.interface_reader.readline()  # Read a line of bytes
            if not data:  # EOF
                break
            cli.model_writer.write(data)
            await cli.model_writer.drain()
    except asyncio.CancelledError:
        # Clean shutdown when task is cancelled
        return

async def pump_model_to_cli(cli):
    """
    Read raw bytes from cli.model_reader and write them to cli.interface_writer.
    No decoding or processing of the byte stream.
    """
    try:
        while True:
            data = await cli.model_reader.readline()  # Read a line of bytes
            if not data:  # EOF
                break
            cli.interface_writer.write(data)
            await cli.interface_writer.drain()
    except asyncio.CancelledError:
        # Clean shutdown when task is cancelled
        return

async def main():
    # 1) Load GPT-2
    gpt2 = GPT2Model()
    ok = await gpt2.load_model()
    if not ok:
        print("❌ GPT-2 failed to load.")
        return
    print("✅ GPT-2 loaded.\n")

    # 2) Create paired sockets for interface <-> model
    sock_a, sock_b = socket.socketpair()

    # 3) Open asyncio streams
    interface_reader, model_writer = await asyncio.open_connection(sock=sock_a)
    model_reader, interface_writer = await asyncio.open_connection(sock=sock_b)

    # 4) Instantiate CLI and attach streams & model
    cli = Cli_Chat(prompt_symbol="> ")
    cli.interface_reader = interface_reader
    cli.model_writer     = model_writer
    cli.interface_writer = interface_writer
    cli.model_reader     = model_reader
    cli._gpt2            = gpt2

    # 5) Define coroutines for pumping data between CLI and model
    async def stdin_to_interface():
        try:
            while True:
                line = await asyncio.to_thread(input, cli.prompt_symbol)
                cli.interface_writer.write((line + "\n").encode())
                await cli.interface_writer.drain()
        except asyncio.CancelledError:
            return

    async def modcon_loop():
        # Create raw byte stream pumps to replace run_event_loop
        cli_to_model = asyncio.create_task(pump_cli_to_model(cli))
        model_to_cli = asyncio.create_task(pump_model_to_cli(cli))
        
        # Wait for any task to complete (EOF or error)
        done, pending = await asyncio.wait(
            [cli_to_model, model_to_cli],
            return_when=asyncio.FIRST_COMPLETED
        )
        
        # Cancel any pending tasks for clean shutdown
        for task in pending:
            task.cancel()
        await asyncio.gather(*pending, return_exceptions=True)
        return False  # Signal to exit

    print("Type your message (or 'exit' to quit):\n")

    # 6) Run both tasks and cancel stdin pump when done
    stdin_task = asyncio.create_task(stdin_to_interface())
    mod_task   = asyncio.create_task(modcon_loop())

    # wait for the controller loop to finish
    await mod_task
    # stop pumping stdin
    stdin_task.cancel()
    await asyncio.gather(stdin_task, return_exceptions=True)

    print("👋 Goodbye!")

if __name__ == "__main__":
    asyncio.run(main())