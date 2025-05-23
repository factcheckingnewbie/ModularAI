#!/usr/bin/env python3
"""
Simplified module_manager that loads x.py,
Entry-point that can either run the normal module or the DebugModule harness.
injects the CLI and model classes, and runs the bridge.
We override the vanilla classes here to print simple stats.
Usage:
  python m.py           # runs normal CLI↔Model bridge
  python m.py --debug   # runs DebugModule harness

"""

import sys
import asyncio
import logging

from interfaces.cli_chat_interface import Cli_Chat
from models.gpt2.gpt2_model import GPT2Model
from x import DebugModule, run_module
# --- instrumentation wrappers ---
def main():
    # Configure logging
    logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s: %(message)s")

    if "--debug" in sys.argv:
        debug = DebugModule(Cli_Chat, GPT2Model)
        asyncio.run(debug.run_tests())
        sys.exit(0)

    # original behavior
    asyncio.run(run_module(Cli_Chat, GPT2Model))

if __name__ == "__main__":
    main()
# class MonitoredCli(Cli_Chat):
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         # Print basic interface stats
#         print(f"[Stats] Interface: {self.__class__.__name__}, prompt_symbol='{self.prompt_symbol}'")
# 
# class MonitoredModel(GPT2Model):
#     async def load_model(self):
#         # Time how long model loading takes
#         start = time.time()
#         ok = await super().load_model()
#         elapsed = time.time() - start
#         print(f"[Stats] Model load time: {elapsed:.2f}s")
#         # Print any other relevant model attributes
#         attrs = {k: v for k, v in self.__dict__.items() if not k.startswith("_")}
#         print(f"[Stats] Model attributes: {attrs}")
#         return ok
# 
# # --- entrypoint ---
# 
# if __name__ == "__main__":
#     # Use our monitored subclasses instead of the originals
#     debug = DebugModule(Cli_Chat, GPT2Model)
#     asyncio.run(run_module(MonitoredCli, MonitoredModel))
