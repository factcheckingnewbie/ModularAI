import os
import sys
import asyncio

# Ensure project root is on PYTHONPATH so our modules can be imported
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from interfaces.cli_chat_interface import Cli_Chat
from models.gpt2.gpt2_model import GPT2Model

class DummyWriter:
    """
    A minimal StreamWriter-like stub that captures user messages from Cli_Chat
    and makes them available to the controller loop.
    """
    def __init__(self):
        self.buffer = bytearray()
    def write(self, data: bytes):
        # accumulate exactly what Cli_Chat writes
        self.buffer.extend(data)
    async def drain(self):
        # no-op
        return
    def is_closing(self):
        return False

async def chat_loop():
    # 1) Load GPT2Model
    model = GPT2Model()
    ok = await model.load_model()
    if not ok:
        print("❌ Failed to load GPT-2 model.")
        return
    print("✅ GPT-2 model loaded.")

    # 2) Create CLI interface
    cli = Cli_Chat(prompt_symbol="> ")
    reader = asyncio.StreamReader()
    writer = DummyWriter()
    await cli.setup_streams(reader, writer)

    # 3) Conversation loop
    print("Type your message (or 'exit' to quit):")
    while True:
        # run one pass: model->interface & user->interface
        await cli.run_event_loop()

        # extract user input that Cli_Chat wrote
        user_text = writer.buffer.decode("utf-8").rstrip("\n")
        writer.buffer.clear()

        if not user_text or user_text.lower() in ("exit", "quit"):
            print("👋 Goodbye!")
            break

        # 4) Generate GPT-2 response
        response = model.generator(user_text, max_length=100)
        # Hugging Face pipeline returns a list of dicts
        if isinstance(response, list) and "generated_text" in response[0]:
            bot_reply = response[0]["generated_text"]
        else:
            bot_reply = str(response)

        # 5) Feed the model reply back into the CLI reader
        reader.feed_data((bot_reply + "\n").encode("utf-8"))
        # ensure EOF so process_model part of run_event_loop doesn't hang
        reader.feed_eof()

if __name__ == "__main__":
    asyncio.run(chat_loop())
