import asyncio
import socket
import os
import sys
import argparse
import json
from datetime import datetime
from models.gpt2.gpt2_model import GPT2Model
from interfaces.cli_chat_interface import Cli_Chat

# gpt2_model = GPT2Model()
# cli_interface = Cli_Chat(prompt_symbol="> ")
# 
# # Print to confirm
# print("Model instance:", gpt2_model)
# print("Interface instance:", cli_interface)



async def create_streams():
    # Create a socket pair (two connected sockets)
    sock_a, sock_b = socket.socketpair()
    
    # Wrap sockets with asyncio streams
    interface_reader, model_writer = await asyncio.open_connection(sock=sock_a)
    model_reader, interface_writer = await asyncio.open_connection(sock=sock_b)
    
    return interface_reader, interface_writer, model_reader, model_writer

def wire_components(interface, model, interface_reader, interface_writer, model_reader, model_writer):
    # Attach streams to the interface
    interface.reader = interface_reader
    interface.writer = interface_writer
    # Attach streams to the model
    model.reader = model_reader
    model.writer = model_writer

async def main():
    # Try to create streams
  # Instantiate
    gpt2_model = GPT2Model()
    cli_interface = Cli_Chat(prompt_symbol="> ")
    # Create streams
    interface_reader, interface_writer, model_reader, model_writer = await create_streams()
    # Wire components
    wire_components(cli_interface, gpt2_model, interface_reader, interface_writer, model_reader, model_writer)
    
    # Print attributes to confirm
    print("Interface.reader:", cli_interface.reader)
    print("Interface.writer:", cli_interface.writer)
    print("Model.reader:", gpt2_model.reader)
    print("Model.writer:", gpt2_model.writer)


    # After wiring...
    await cli_interface.writer.drain()
    cli_interface.writer.write(b"hello model\n")
    await cli_interface.writer.drain()
    msg = await gpt2_model.reader.readline()
    print("Model received:", msg)
    
    
    # Clean up (close writers)
    interface_writer.close()
    model_writer.close()
    await interface_writer.wait_closed()
    await model_writer.wait_closed()
    
if __name__ == "__main__":
    asyncio.run(main())
