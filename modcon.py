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

async def pump(src_reader, dst_writer):
    """
    Generic raw‐byte pump: read chunks from src_reader and write them to dst_writer.
    """
    try:
        while True:
            chunk = await src_reader.read(1024)
            if not chunk:
                break
            dst_writer.write(chunk)
            await dst_writer.drain()
    except asyncio.CancelledError:
        pass

async def run_module(InterfaceCls, ModelCls):
    """
    Instantiate and wire up frontend interface & backend model, then shuttle raw data.
    """
    # 1) Instantiate and load model
    model = ModelCls()
    ok = await model.load_model()
    if not ok:
        print("❌ Model failed to load.")
        return
    print("✅ Model loaded.\n")

    # 2) Build raw streams
    interface_reader, interface_writer, model_reader, model_writer = await create_streams()

    # 3) Instantiate frontend and attach streams
    interface = InterfaceCls()
    wire_components(interface, model,
                    interface_reader, interface_writer,
                    model_reader, model_writer)

    # 4) Set up bidirectional pumps
    task_frontend = asyncio.create_task(
        pump(interface.reader, interface.backend_writer)
    )
    task_backend = asyncio.create_task(
        pump(model.reader, model.frontend_writer)
    )

    # 5) Wait until one side closes, then cancel the other
    done, pending = await asyncio.wait(
        [task_frontend, task_backend],
        return_when=asyncio.FIRST_COMPLETED,
    )
    for t in pending:
        t.cancel()
    await asyncio.gather(*pending, return_exceptions=True)

    print("👋 Goodbye!")

