#!/usr/bin/env python3
"""
Simplified module_manager that loads modcon.py,
injects the CLI and model classes, and runs the bridge.
  python modman.py           # runs normal CLI↔Model bridge
"""

import sys
import time
import asyncio
import logging

from interfaces.cli_chat_interface import Cli_Chat
from models.gpt2.gpt2_model import GPT2Model

async def test_modular_connection():
    model = GPT2Model()         
    interface = Cli_Chat()      
    connection = await connect_model_and_interface(model, interface)

from modconNew import run_module
def main():

    asyncio.run(run_module(Cli_Chat, GPT2Model))
if __name__ == "__main__":
    main()

