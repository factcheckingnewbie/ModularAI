#!/usr/bin/env python3
"""
Simplified module_manager that loads x.py,
injects the CLI and model classes, and runs the bridge.
We override the vanilla classes here to print simple stats.
"""

import asyncio
import time

from interfaces.cli_chat_interface import Cli_Chat
from models.gpt2.gpt2_model import GPT2Model
from x import run_module

# --- instrumentation wrappers ---

class MonitoredCli(Cli_Chat):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Print basic interface stats
        print(f"[Stats] Interface: {self.__class__.__name__}, prompt_symbol='{self.prompt_symbol}'")

class MonitoredModel(GPT2Model):
    async def load_model(self):
        # Time how long model loading takes
        start = time.time()
        ok = await super().load_model()
        elapsed = time.time() - start
        print(f"[Stats] Model load time: {elapsed:.2f}s")
        # Print any other relevant model attributes
        attrs = {k: v for k, v in self.__dict__.items() if not k.startswith("_")}
        print(f"[Stats] Model attributes: {attrs}")
        return ok

# --- entrypoint ---

if __name__ == "__main__":
    # Use our monitored subclasses instead of the originals
    asyncio.run(run_module(MonitoredCli, MonitoredModel))
