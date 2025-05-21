import os
import sys

# ensure project root is on PYTHONPATH so 'interfaces' can be imported
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import asyncio
import pytest
from interfaces.cli_chat_interface import Cli_Chat

# print("output before eventloop")
async def run_event_loop(self):
    # 1) Model -> Interface (one shot)
    if hasattr(self, 'reader') and self.reader:
        try:
            data = await asyncio.wait_for(self.reader.readline(), timeout=0.5)
            if data:
                print(data.decode('utf-8').rstrip('\n'))
        except asyncio.TimeoutError:
            pass

    # 2) User -> Model: attempt to read inputs via to_thread+timeout, then exit
    while True:
        try:
            # run input() in a thread so we can timeout if it's blocking
            user_input = await asyncio.wait_for(
                asyncio.to_thread(input, self.prompt_symbol),
                timeout=0.1
            )
        except asyncio.TimeoutError:
            # no more inputs available, exit
            break
        if not user_input:
            break
        self.writer.write((user_input + "\n").encode('utf-8'))
        await self.writer.drain()

    return
def test_model_to_interface_prints_message(capsys):
    """
    Feed a line into the interface's reader and ensure it gets printed
    to stdout by the CLIChatInterface.
    """
    async def runner():
        reader = asyncio.StreamReader()
        writer = DummyWriter()
        interface = Cli_Chat(prompt_symbol="> ")
        await interface.setup_streams(reader, writer)

        # Simulate model sending a message
        test_line = "Model says hello\n".encode('utf-8')
        reader.feed_data(test_line)
        reader.feed_eof()

        # Run the interface loop briefly
#        print("0.1 before: task = asyncio.create_task(interface.run_event_loop())")
        task = asyncio.create_task(interface.run_event_loop())
#        print("0.2 before: await asyncio.sleep(0.5)")
        await asyncio.sleep(0.5)
        # ensure the task completes
        await task

    asyncio.run(runner())
    captured = capsys.readouterr()
    assert "Model says hello" in captured.out

def test_user_input_writes_to_writer(monkeypatch):
    """
    Monkey-patch builtins.input to simulate two user inputs,
    then verify that they are sent (with newline) to the controller via writer.
    """
    async def runner():
        reader = asyncio.StreamReader()
        writer = DummyWriter()
        interface = Cli_Chat(prompt_symbol="> ")
        await interface.setup_streams(reader, writer)

        # Prepare two inputs, then stop
        inputs = ["first message", "second message"]
        monkeypatch.setattr('builtins.input', lambda prompt: inputs.pop(0) if inputs else "")

        # Run the interface loop briefly
#        print("1. Before: task = asyncio.create_task(interface.run_event_loop())")
        task = asyncio.create_task(interface.run_event_loop())
        await asyncio.sleep(0.5)
        await task

        # Verify that both messages (with newline) were written out
        written = writer.buffer.decode('utf-8')
        assert "first message\n" in written
        assert "second message\n" in written

    asyncio.run(runner())
