import os
import sys
import asyncio
import io
import builtins

# Ensure project root is on PYTHONPATH so 'interfaces' can be imported
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from interfaces.cli_chat_interface import Cli_Chat

class DummyWriter:
    """
    A simple StreamWriter-like stub that captures written bytes
    and provides an async drain().
    """
    def __init__(self):
        self.buffer = bytearray()
    def write(self, data: bytes):
        self.buffer.extend(data)
    async def drain(self):
        # no-op for tests
        return
    def is_closing(self):
        return False

async def test_model_to_interface():
    """
    Test that text from the model (reader) is printed to stdout.
    """
    reader = asyncio.StreamReader()
    writer = DummyWriter()
    interface = Cli_Chat(prompt_symbol="> ")
    await interface.setup_streams(reader, writer)

    # Prepare a line from the "model"
    model_line = "Model says hello\n".encode("utf-8")
    reader.feed_data(model_line)
    reader.feed_eof()

    # Capture stdout
    orig_stdout = sys.stdout
    sys.stdout = io.StringIO()

    # Run one iteration of the CLI loop
    # (our interface.run_event_loop exits after one line + user phase)
    await interface.run_event_loop()

    output = sys.stdout.getvalue().strip()
    sys.stdout = orig_stdout

    if "Model says hello" in output:
        print("✅ test_model_to_interface: PASS")
    else:
        print("❌ test_model_to_interface: FAIL")
        print("Captured output:", repr(output))

async def test_user_input_writes_to_writer():
    """
    Test that user input() calls are written (with newline) to the controller via writer.
    """
    reader = asyncio.StreamReader()
    writer = DummyWriter()
    interface = Cli_Chat(prompt_symbol="> ")
    await interface.setup_streams(reader, writer)

    # Monkey-patch input() to simulate two lines, then empty to exit
    inputs = ["first message", "second message", ""]
    builtins_input = builtins.input
    builtins.input = lambda prompt="": inputs.pop(0)

    # Run one iteration of the CLI loop
    await interface.run_event_loop()

    # Restore input()
    builtins.input = builtins_input

    sent = writer.buffer.decode("utf-8").splitlines()
    if sent == ["first message", "second message"]:
        print("✅ test_user_input_writes_to_writer: PASS")
    else:
        print("❌ test_user_input_writes_to_writer: FAIL")
        print("Writer buffer:", sent)

async def main():
    await test_model_to_interface()
    await test_user_input_writes_to_writer()

if __name__ == "__main__":
    asyncio.run(main())
