#!/usr/bin/env python3
"""
Next iteration: fix the gather logic so only one consumer
reads from interface_reader. We split into two coroutines:

  - stdin_to_interface(): pumps user input into interface_writer
  - modcon_loop(): repeatedly calls run_event_loop()

We avoid concurrent .readline() calls on the same reader.
"""

import os
import sys
import asyncio
import socket

# ensure project root is on PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from interfaces.cli_chat_interface import Cli_Chat
from models.gpt2.gpt2_model import GPT2Model

async def run_event_loop(self):
    line = await self.interface_reader.readline()
    if not line:
        return False
    text = line.decode().rstrip("\n")
    if text.lower() in ("exit", "quit"):
        return False

    # send through HF pipeline
    resp = self._gpt2.generator(
        text,
        max_new_tokens=100,
        truncation=True
    )
    # extract
    if isinstance(resp, list) and resp and "generated_text" in resp[0]:
        out = resp[0]["generated_text"]
    else:
        out = str(resp)

    self.model_writer.write((out + "\n").encode())
    await self.model_writer.drain()
    return True

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
    sock_c, sock_d = socket.socketpair()

    # 3) Open asyncio streams
    interface_reader, model_writer = await asyncio.open_connection(sock=sock_a)
    model_reader, interface_writer = await asyncio.open_connection(sock=sock_b)

    # 4) Instantiate CLI and attach streams & model
    cli = Cli_Chat(prompt_symbol="> ")
    cli.interface_reader = interface_reader
    cli.model_writer     = model_writer
    cli.interface_writer = interface_writer  # for stdin pump
    cli.model_reader     = model_reader     # for model pump
    cli._gpt2            = gpt2

    # 5) Monkey-patch our relay loop
    Cli_Chat.run_event_loop = run_event_loop

    # 6) Define the three tasks
    async def stdin_to_interface():
        try:
            while True:
                line = await asyncio.to_thread(input, cli.prompt_symbol)
                interface_writer.write((line + "\n").encode())
                await interface_writer.drain()
        except asyncio.CancelledError:
            return

    async def pump_model():
        try:
            while True:
                line = await cli.model_reader.readline()
                if line:
                    print(line.decode().rstrip("\n"))
        except asyncio.CancelledError:
            return

    async def controller_loop():
        # drive the patched run_event_loop until it returns False
        while await cli.run_event_loop():
            pass

    print("Type your message (or 'exit' to quit):\n")

    # 7) Run all tasks and ensure proper cancellation
    stdin_task = asyncio.create_task(stdin_to_interface())
    model_task = asyncio.create_task(pump_model())
    controller_task = asyncio.create_task(controller_loop())

    # Wait for the controller loop to finish
    try:
        await controller_task
    finally:
        # Cancel both pump tasks
        stdin_task.cancel()
        model_task.cancel()
        # Wait for them to complete cancellation
        await asyncio.gather(stdin_task, model_task, return_exceptions=True)

    print("👋 Goodbye!")

if __name__ == "__main__":
    asyncio.run(main())