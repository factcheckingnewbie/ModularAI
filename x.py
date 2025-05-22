#!/usr/bin/env python3
"""
Core runner that ties a CLI interface and GPT-2 model together.
Exposes a single async function `run_module` but does not execute on its own.
"""

import asyncio
import socket
from asyncio import StreamReader, StreamWriter

async def create_streams():
    """
    Set up socketpairs and open asyncio streams for communication between components.
    
    Returns:
        Tuple: (interface_reader, interface_writer, model_reader, model_writer)
    """
    sock_a, sock_b = socket.socketpair()
    interface_reader, model_writer = await asyncio.open_connection(sock=sock_a)
    model_reader, interface_writer = await asyncio.open_connection(sock=sock_b)
    
    return interface_reader, interface_writer, model_reader, model_writer

def wire_components(interface, model, interface_reader, interface_writer, model_reader, model_writer):
    """
    Attach streams to interface and model using standardized methods.
    
    Args:
        interface: The interface component instance
        model: The model component instance
        interface_reader: StreamReader for interface reading
        interface_writer: StreamWriter for interface writing
        model_reader: StreamReader for model reading
        model_writer: StreamWriter for model writing
    """
    # Attach streams to interface
    # The interface needs both reader/writer pairs
    interface.interface_reader = interface_reader
    interface.interface_writer = interface_writer
    interface.model_reader = model_reader
    interface.model_writer = model_writer
    
    # Attach model reference to interface (required for current implementation)
    interface._gpt2 = model
    
    # Attach streams to model (using standard method)
    model.set_streams(model_reader, model_writer)

async def run_event_loop(self):
    """
    Reads one line from self.interface_reader, generates a reply with GPT-2,
    writes it to self.model_writer, and returns False on EOF or exit.
    """
    data = await self.interface_reader.readline()
    if not data:
        return False

    text = data.decode().rstrip("\n")
    if text.strip().lower() in ("exit", "quit"):
        return False

    # Generate with GPT-2
    response = self._gpt2.generator(
        text,
        max_new_tokens=100,
        truncation=True
    )
    # Extract generated_text
    if isinstance(response, list) and response and "generated_text" in response[0]:
        reply = response[0]["generated_text"]
    else:
        reply = str(response)

    self.model_writer.write((reply + "\n").encode())
    await self.model_writer.drain()
    return True

async def run_module(Cli_Chat, GPT2Model):
    """
    Instantiate and wire up CLI + GPT-2, then pump stdin ↔ CLI ↔ model.
    """
    # 1) Load GPT-2
    gpt2 = GPT2Model()
    ok = await gpt2.load_model()
    if not ok:
        print("❌ GPT-2 failed to load.")
        return
    print("✅ GPT-2 loaded.\n")

    # 2) Create streams for communication
    interface_reader, interface_writer, model_reader, model_writer = await create_streams()

    # 3) Instantiate CLI and attach streams + model
    cli = Cli_Chat(prompt_symbol="> ")
    
    # 4) Wire up components
    wire_components(cli, gpt2, interface_reader, interface_writer, model_reader, model_writer)

    # 5) Monkey-patch our relay loop
    Cli_Chat.run_event_loop = run_event_loop

    # 5) Define pump/loop tasks
    async def pump_stdin():
        try:
            while True:
                line = await asyncio.to_thread(input, cli.prompt_symbol)
                interface_writer.write((line + "\n").encode())
                await interface_writer.drain()
        except asyncio.CancelledError:
            return

    async def controller_loop():
        while await cli.run_event_loop():
            pass

    # 6) Run until exit
    pump_task = asyncio.create_task(pump_stdin())
    ctrl_task = asyncio.create_task(controller_loop())

    await ctrl_task
    pump_task.cancel()
    await asyncio.gather(pump_task, return_exceptions=True)

    print("👋 Goodbye!")
