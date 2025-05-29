import asyncio
import socket
import json
from models.gpt2.gpt2_model import GPT2Model
from interfaces.cli_chat_interface import Cli_Chat

async def create_streams():
    sock_a, sock_b = socket.socketpair()
    # Side A (interface)
    interface_reader, interface_writer = await asyncio.open_connection(sock=sock_a)
    # Side B (model)
    model_reader, model_writer = await asyncio.open_connection(sock=sock_b)
    return interface_reader, interface_writer, model_reader, model_writer

def wire_components(interface, model, interface_reader, interface_writer, model_reader, model_writer):
    # Correct cross-connection!
    interface.reader = model_reader
    interface.writer = model_writer
    model.reader = interface_reader
    model.writer = interface_writer

async def main():
    gpt2_model = GPT2Model()
    cli_interface = Cli_Chat(prompt_symbol="> ")
    interface_reader, interface_writer, model_reader, model_writer = await create_streams()
    wire_components(cli_interface, gpt2_model, interface_reader, interface_writer, model_reader, model_writer)

    # Start the model's run loop in the background
    model_task = asyncio.create_task(gpt2_model.run())

    # Now the interface (controller) should receive the capabilities
    capabilities_msg = await cli_interface.reader.readline()
    print("Controller received model capabilities:", capabilities_msg.decode().strip())

    # Send a prompt from the interface to the model
    prompt = "Hello, world!"
    request = {
        "message_type": "text_generation",
        "prompt": prompt,
        "request_id": "test1"
    }
    json_msg = json.dumps(request) + "\n"
    cli_interface.writer.write(json_msg.encode("utf-8"))
    await cli_interface.writer.drain()

    # Read the model's response from the interface's reader
    response = await cli_interface.reader.readline()
    print("Interface received:", response.decode())

    # Clean up
    model_task.cancel()
    try:
        await model_task
    except asyncio.CancelledError:
        pass
    interface_writer.close()
    model_writer.close()
    await interface_writer.wait_closed()
    await model_writer.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())
