#!/usr/bin/env python3
"""
Core runner that ties a frontend interface and backend model together.
Exposes a single async function `run_module` but does not execute on its own.
"""

import sys
import time
import asyncio
import socket
import logging

async def create_streams():
    """
    Create paired socket streams and return:
      (interface_reader, interface_writer, model_reader, model_writer)
    """
    sock_a, sock_b = socket.socketpair()
    interface_reader, model_writer = await asyncio.open_connection(sock=sock_a)
    model_reader, interface_writer = await asyncio.open_connection(sock=sock_b)
    return interface_reader, interface_writer, model_reader, model_writer

def wire_components(interface, model,
                    interface_reader, interface_writer,
                    model_reader, model_writer):
    """
    Attach raw stream endpoints to the interface and model objects.
    - interface.reader/writer communicate with the front end (e.g. CLI)
    - model.reader/writer communicate with the backend (e.g. GPT-2)
    """
    interface.reader = interface_reader
    interface.writer = interface_writer
    interface.backend_reader = model_reader
    interface.backend_writer = model_writer

    model.reader = model_reader
    model.writer = model_writer
    model.frontend_reader = interface_reader
    model.frontend_writer = interface_writer


async def run_module(InterfaceCls, ModelCls):
    # 1) Load Model
    model = ModelCls()
    ok = await model.load_model()
    if not ok:
        print("❌ Model failed to load.")
        return
    print("✅ Model loaded.\n")

    # 2) Build paired streams
    interface_reader, interface_writer, model_reader, model_writer = await create_streams()

    # 3) Instantiate frontend and attach streams
    interface = InterfaceCls()
    await interface.setup_streams(interface_reader, interface_writer)
    model.set_streams(model_reader, model_writer)

    # 4) Run both main loops concurrently
    await asyncio.gather(
        interface.run(),
        model.run(),
    )
