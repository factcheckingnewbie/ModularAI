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
    Uses cross-connection so interface and model communicate robustly.
    """
    sock_a, sock_b = socket.socketpair()
    # Side A (interface)
    interface_reader, interface_writer = await asyncio.open_connection(sock=sock_a)
    # Side B (model)
    model_reader, model_writer = await asyncio.open_connection(sock=sock_b)
    return interface_reader, interface_writer, model_reader, model_writer

def wire_components(interface, model, interface_reader, interface_writer, model_reader, model_writer):
    """
    Attach raw stream endpoints to the interface and model objects.
    Each gets its own reader/writer pair, not cross-connected.
    """
    # Interface uses its own reader/writer for CLI<->controller
    interface.reader = interface_reader
    interface.writer = interface_writer
    # Model uses its own reader/writer for controller<->model
    model.reader = model_reader
    model.writer = model_writer

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

    # 4) Start the model's run loop in the background
    model_task = asyncio.create_task(model.run())
    # Read capabilities message from model before starting model.run()
    capabilities_msg = await model_reader.readline()
    print("Controller received model capabilities:", capabilities_msg.decode().strip())
    model_task = asyncio.create_task(model.run())

    # 6) Set up bidirectional pumps for ongoing communication (optional, legacy support)
    # If you want to pump raw bytes concurrently, uncomment below:
    # task_frontend = asyncio.create_task(pump(interface.reader, interface.writer))
    # task_backend = asyncio.create_task(pump(model.reader, model.writer))
    # done, pending = await asyncio.wait(
    #     [task_frontend, task_backend],
    #     return_when=asyncio.FIRST_COMPLETED,
    # )
    # for t in pending:
    #     t.cancel()
    # await asyncio.gather(*pending, return_exceptions=True)
