import asyncio
import pytest
from interfaces.cli_chat_interface import CliP

class DummyWriter:
    """
    A simple StreamWriter-like stub that captures written bytes
    and provides a no-op drain().
    """
    def __init__(self):
        self.buffer = bytearray()

    def write(self, data: bytes):
        self.buffer.extend(data)

    def is_closing(self) -> bool:
        return False

    async def drain(self):
        # no-op for testing
        pass

@pytest.mark.asyncio
async def test_model_to_interface_prints_message(capsys):
    """
    Feed a line into the interface's reader and ensure it gets printed
    to stdout by the CLIChatInterface.
    """
    reader = asyncio.StreamReader()
    writer = DummyWriter()
    interface = CLIChatInterface(prompt_symbol="> ")
    interface.set_streams(reader, writer)

    # Simulate model sending a message
    test_line = "Model says hello\n".encode('utf-8')
    reader.feed_data(test_line)
    reader.feed_eof()

    # Run the interface loop briefly
    task = asyncio.create_task(interface.run_event_loop())
    # let it process the fed data
    await asyncio.sleep(0.1)
    task.cancel()

    # Capture stdout and verify printed output
    captured = capsys.readouterr()
    assert "Model says hello" in captured.out

@pytest.mark.asyncio
async def test_user_input_writes_to_writer(monkeypatch):
    """
    Monkey-patch builtins.input to simulate two user inputs,
    then verify that they are sent (with newline) to the controller via writer.
    """
    reader = asyncio.StreamReader()
    writer = DummyWriter()
    interface = CLIChatInterface(prompt_symbol="> ")
    interface.set_streams(reader, writer)

    # Prepare two inputs, then stop
    inputs = ["first message", "second message"]
    monkeypatch.setattr('builtins.input', lambda prompt: inputs.pop(0) if inputs else "")

    # Run the interface loop briefly
    task = asyncio.create_task(interface.run_event_loop())
    await asyncio.sleep(0.1)
    task.cancel()

    # Verify that both messages (with newline) were written out
    written = writer.buffer.decode('utf-8')
    assert "first message\n" in written
    assert "second message\n" in written
