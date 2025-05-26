import os
import sys
import asyncio

# ensure project root is on PYTHONPATH so 'interfaces' can be imported
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from interfaces.cli_chat_interface import Cli_Chat
from models.gpt2.gpt2_model import GPT2Model

async def run_event_loop(self):
    """
    One-shot loop:
      - prompt the user
      - send input to GPT-2
      - print GPT-2 reply
    Return False when user wants to quit.
    """
    # 1) prompt user
    try:
        user_input = await asyncio.to_thread(input, self.prompt_symbol)
    except EOFError:
        return False

    if not user_input or user_input.strip().lower() in ("exit", "quit"):
        return False

    # 2) generate with GPT-2
    response = self._gpt2.generator(user_input, max_length=100)
    # HuggingFace pipeline returns list of dicts
    if isinstance(response, list) and response and "generated_text" in response[0]:
        reply = response[0]["generated_text"]
    else:
        reply = str(response)

    # 3) print GPT-2 reply
    print("\n" + reply + "\n")
    return True

async def main():
    # 1) Load GPT-2
    gpt2 = GPT2Model()
    ok = await gpt2.load_model()
    if not ok:
        print("❌ GPT-2 failed to load. Check your transformers install.")
        return
    print("✅ GPT-2 loaded successfully.\n")

    # 2) Prepare CLI wrapper
    cli = Cli_Chat(prompt_symbol="> ")
    # attach model instance to cli
    cli._gpt2 = gpt2
    # monkey-patch our simple run_event_loop
    Cli_Chat.run_event_loop = run_event_loop

    print("Type your message (or 'exit' to quit):\n")

    # 3) Loop until user quits
    while await cli.run_event_loop():
        pass

    print("👋 Goodbye!")

if __name__ == "__main__":
    asyncio.run(main())
