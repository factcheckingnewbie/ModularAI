#!/usr/bin/env python3
"""
A new ModuleController that skips ModuleManager/configs,
wiring up exactly the CLI <-> GPT2Model bridge we validated in modcon_tmp.py.

This will let us confirm the fix in a “real” controller before
we merge it back into module_manager.py.
"""

import os
import sys
import asyncio
import socket

# ─── ensure project root is on PYTHONPATH ───────────────────────
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from interfaces.cli_chat_interface import Cli_Chat
from models.gpt2.gpt2_model import GPT2Model

class ModuleController:
    def __init__(self):
        self.cli = None
        self.gpt2 = None

    async def setup(self):
        # 1) Load GPT-2
        self.gpt2 = GPT2Model()
        ok = await self.gpt2.load_model()
        if not ok:
            print("❌ GPT-2 failed to load. Check transformers install.")
            return False
        print("✅ GPT-2 loaded.\n")

        # 2) Create socket-pair streams
        a, b = socket.socketpair()
        # CLI writes to b (interface_writer), reads from a (interface_reader)
        interface_reader, model_writer = await asyncio.open_connection(sock=a)
        model_reader, interface_writer = await asyncio.open_connection(sock=b)

        # 3) Wire CLI
        self.cli = Cli_Chat(prompt_symbol="> ")
        self.cli.interface_reader = interface_reader
        self.cli.interface_writer = interface_writer
        self.cli.model_reader     = model_reader
        self.cli.model_writer     = model_writer
        # attach model
        self.cli._gpt2 = self.gpt2

        # 4) Patch the loop
        Cli_Chat.run_event_loop = self._run_event_loop
        return True

    async def _run_event_loop(self):
        """
        Consumes one line from interface_reader,
        sends to GPT-2, writes reply to model_writer.
        """
        line = await self.cli.interface_reader.readline()
        if not line:
            return False
        text = line.decode().rstrip("\n")
        if text.lower() in ("exit", "quit"):
            return False

        # send through HF pipeline
        resp = self.cli._gpt2.generator(
            text,
            max_new_tokens=100,
            truncation=True
        )
        # extract
        if isinstance(resp, list) and resp and "generated_text" in resp[0]:
            out = resp[0]["generated_text"]
        else:
            out = str(resp)

        self.cli.model_writer.write((out + "\n").encode())
        await self.cli.model_writer.drain()
        return True

    async def run(self):
        # pump stdin into CLI
        async def stdin_pump():
            try:
                while True:
                    msg = await asyncio.to_thread(input, self.cli.prompt_symbol)
                    self.cli.interface_writer.write((msg + "\n").encode())
                    await self.cli.interface_writer.drain()
            except asyncio.CancelledError:
                pass

        # controller loop
        async def controller_loop():
            while await self.cli.run_event_loop():
                pass

        print("Type message (or 'exit' to quit):\n")
        pump = asyncio.create_task(stdin_pump())
        loop = asyncio.create_task(controller_loop())

        await loop
        pump.cancel()
        await asyncio.gather(pump, return_exceptions=True)
        print("👋 Goodbye!")

async def main():
    mc = ModuleController()
    if not await mc.setup():
        return
    await mc.run()

if __name__ == "__main__":
    asyncio.run(main())
