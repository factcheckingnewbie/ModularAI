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
    """
    Reads from self.interface_reader, writes to self.model_writer,
    then invokes GPT-2. Returns False on EOF or 'exit'.
    """
    data = await self.interface_reader.readline()
    if not data:
        return False

    user_input = data.decode().rstrip("\n")
    if user_input.strip().lower() in ("exit", "quit"):
        return False

    # generate reply
    response = self._gpt2.generator(
        user_input,
        max_new_tokens=100,
        truncation=True
    )

    if isinstance(response, list) and response and "generated_text" in response[0]:
        reply = response[0]["generated_text"]
    else:
        reply = str(response)

    # write reply into model_writer
    self.model_writer.write((reply + "\n").encode())
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
    cli.model_reader     = model_reader     # now used by pump_model()
    cli._gpt2            = gpt2

    # 5) Monkey-patch our relay loop
    Cli_Chat.run_event_loop = run_event_loop

    # 6) Define the tasks
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
                data = await cli.model_reader.readline()
                if not data:  # EOF
                    break
                # Print the model's response to stdout
                print(data.decode().rstrip("\n"))
        except asyncio.CancelledError:
            return

    async def modcon_loop():
        # drive the patched run_event_loop until it returns False
        while await cli.run_event_loop():
            pass
            
    print("Type your message (or 'exit' to quit):\n")

    # 7) Run all three tasks and cancel them properly when done
    stdin_task = asyncio.create_task(stdin_to_interface())
    model_task = asyncio.create_task(pump_model())
    mod_task   = asyncio.create_task(modcon_loop())

    # wait for the controller loop to finish
    await mod_task
    # stop the other tasks
    stdin_task.cancel()
    model_task.cancel()
    await asyncio.gather(stdin_task, model_task, return_exceptions=True)

    print("👋 Goodbye!")

if __name__ == "__main__":
    asyncio.run(main())