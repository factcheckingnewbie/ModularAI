#!/usr/bin/env python3
"""
Simple script to run the x.py file which contains the
main implementation of the ModularAI chat interface.
"""

import os
import sys
import asyncio
import x

if __name__ == "__main__":
    # Simply import and run x.py
    print("Starting ModularAI chat interface...")
    asyncio.run(x.main())