#!/usr/bin/env python3
"""
Minimal ModuleController based on chat_cli_bridge.py

This “modcon_tmp” skips module_manager and config scanning.
It wires up exactly two fixed modules:
  • interfaces/cli_chat_interface.Cli_Chat
  • models/gpt2/gpt2_model.GPT2Model

We’ll iterate on this until we isolate the AttributeError in streams.
"""

import os
import sys
import asyncio

# ─── ensure project root is on PYTHONPATH so interfaces/models import correctly
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from interfaces.cli_chat_interface import Cli_Chat
from models.gpt2.gpt2_model import GPT2Model

async def run_event_loop(self):
    """
    One-shot loop:
      1) prompt the user
      2) send input to GPT-2
      3) print GPT-2 reply
    Returns False when user wants to quit.
    """
    # 1) prompt user (offload to thread so as not to block loop)
    try:
        user_input = await asyncio.to_thread(input, self.prompt_symbol)
    except EOFError:
        return False

    if not user_input or user_input.strip().lower() in ("exit", "quit"):
        return False

    # 2) generate with GPT-2
    response = self._gpt2.generator(user_input, max_length=100)
    # HuggingFace pipeline returns list of dicts
    if isinstance(response, list) and response and "generated_text" in response[0]:
        reply = response[0]["generated_text"]
    else:
        reply = str(response)

    # 3) print GPT-2 reply
    print("\n" + reply + "\n")
    return True

async def main():
    # 1) Load GPT-2 model
    gpt2 = GPT2Model()
    ok = await gpt2.load_model()
    if not ok:
        print("❌ GPT-2 failed to load. Check your transformers install.")
        return
    print("✅ GPT-2 loaded successfully.\n")

    # 2) Instantiate CLI interface
    cli = Cli_Chat(prompt_symbol="> ")
    # attach model instance to cli for our patched loop
    cli._gpt2 = gpt2
    # override run_event_loop with our minimal loop
    Cli_Chat.run_event_loop = run_event_loop

    print("Type your message (or 'exit' to quit):\n")

    # 3) Loop until user quits
    while await cli.run_event_loop():
        pass

    print("👋 Goodbye!")

if __name__ == "__main__":
    asyncio.run(main())
