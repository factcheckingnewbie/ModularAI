#!/usr/bin/env python3
"""
Simple entry point for ModularAI that uses the simplified x.py module.
"""

import asyncio
from x import run_module

if __name__ == "__main__":
    asyncio.run(run_module())