import asyncio
import pytest
from interfaces.cli_chat_interface import  Cli_Chat

# --- Provide a simple event loop in the test ---
async def run_event_loop(self):
    """
    Simplified loop for testing:
      1) Read from model reader (short timeout) and print to stdout
      2) Call builtin input() for user input, write to the model writer
    """
    while True:
        # 1) Model -> Interface
        if hasattr(self, 'reader') and self.reader:
            try:
                data = await asyncio.wait_for(self.reader.readline(), timeout=0.1)
                if data:
                    # strip newline, print
                    print(data.decode('utf-8').rstrip('\n'))
            except asyncio.TimeoutError:
                pass

        # 2) User -> Model
        try:
            user_input = input(self.prompt_symbol)
        except EOFError:
            user_input = ""
        if user_input:
            self.writer.write((user_input + "\n").encode('utf-8'))
            await self.writer.drain()

        # yield control
        print("abc")
        await asyncio.sleep(1)

# Monkey-patch the interface class for tests
Cli_Chat.run_event_loop = run_event_loop

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
        print("abc")
        pass

@pytest.mark.asyncio
async def test_model_to_interface_prints_message(capsys):
    """
    Feed a line into the interface's reader and ensure it gets printed
    to stdout by the CLIChatInterface.
    """
    reader = asyncio.StreamReader()
    writer = DummyWriter()
    interface = Cli_Chat(prompt_symbol="> ")
    await interface.setup_streams(reader, writer)

    # Simulate model sending a message
    test_line = "Model says hello\n".encode('utf-8')
    reader.feed_data(test_line)
    reader.feed_eof()

    # Run the interface loop briefly
    print("abc")
    task = asyncio.create_task(interface.run_event_loop())
    # let it process the fed data
    await asyncio.sleep(1)
    # task.cancel()

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
    interface = Cli_Chat(prompt_symbol="> ")
    await interface.setup_streams(reader, writer)

    # Prepare two inputs, then stop
    inputs = ["first message", "second message"]
    monkeypatch.setattr('builtins.input', lambda prompt: inputs.pop(0) if inputs else "")

    # Run the interface loop briefly
    print("abc")
    task = asyncio.create_task(interface.run_event_loop())
    await asyncio.sleep(1)
   # task.cancel()

    # Verify that both messages (with newline) were written out
    written = writer.buffer.decode('utf-8')
    assert "first message\n" in written
    assert "second message\n" in written
