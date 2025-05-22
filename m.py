#!/usr/bin/env python3
"""
Simplified module_manager that loads x.py,
injects the CLI and model classes, and runs the bridge.
"""

import asyncio
from interfaces.cli_chat_interface import Cli_Chat
from models.gpt2.gpt2_model import GPT2Model
from x import run_module

if __name__ == "__main__":
    asyncio.run(run_module(Cli_Chat, GPT2Model))
