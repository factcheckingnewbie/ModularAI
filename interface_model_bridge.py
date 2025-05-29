import os
import sys
import asyncio
import argparse
import json
from datetime import datetime
from models.gpt2.gpt2_model import GPT2Model
from interfaces.cli_chat_interface import Cli_Chat

gpt2_model = GPT2Model()
cli_interface = Cli_Chat(prompt_symbol="> ")

# Print to confirm
print("Model instance:", gpt2_model)
print("Interface instance:", cli_interface)

exit()


# ensure project root is on PYTHONPATH so 'interfaces' can be imported
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from interfaces.cli_chat_interface import Cli_Chat
from models.gpt2.gpt2_model import GPT2Model

LOG_FILE = "progname.log"

class Logger:
    def __init__(self, mode):
        self.mode = mode
        self.log_file = LOG_FILE
        self.fh = open(self.log_file, "a", encoding="utf-8") if mode in ("log", "both") else None

    def timestamp(self):
        return datetime.now().strftime("%Y-%m-%d %H-%M-%S")

    def log(self, msg):
        entry = f"{msg} [{self.timestamp()}]"
        if self.mode in ("tty", "both"):
            print(entry)
        if self.fh:
            self.fh.write(entry + "\n")
            self.fh.flush()

    def close(self):
        if self.fh:
            self.fh.close()

def is_json(text):
    try:
        return json.loads(text)
    except Exception:
        return None

async def run_event_loop(self, logger):
    try:
        user_input = await asyncio.to_thread(input, self.prompt_symbol)
    except EOFError:
        return False

    if not user_input or user_input.strip().lower() in ("exit", "quit"):
        return False
    json_obj = is_json(user_input)
    
    if json_obj is not None:
    # Control: Only log valid JSON expectations and sent data
        if isinstance(json_obj, dict) or isinstance(json_obj, list):
            logger.log(f'JSON expected: {json.dumps(json_obj)}')
            logger.log(f'JSON sent: {json.dumps(json_obj)}')
            logger.log('JSON expected: <json>')
        else:
            logger.log('JSON expected: <invalid json>')
            logger.log('JSON sent: <invalid json>')
            logger.log('JSON expected: <json>')
    else:
        # Control: Only log if input is a non-empty string and not JSON
        if isinstance(user_input, str) and user_input.strip() != "":
            logger.log(f'String expected: {user_input}')
            logger.log(f'String sent: {user_input}')
            logger.log('String expected: <string>')
        else:
            logger.log('String expected: <invalid or empty input>')
            logger.log('String sent: <invalid or empty input>')
            logger.log('String expected: <string>')


        response = self._gpt2.generator(user_input, max_length=100)
    if isinstance(response, list) and response and "generated_text" in response[0]:
        reply = response[0]["generated_text"]
    else:
        reply = str(response)

    reply_json = is_json(reply)
    if reply_json is not None:
        logger.log(f'JSON received: {json.dumps(reply_json)}')
    else:
        logger.log(f'String received: {reply}')

    print("\n" + reply + "\n")
    return True

async def main():
    parser = argparse.ArgumentParser(description="Debug/test harness for ModularAI interface and model communication.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--log", action="store_true", help="Log to progname.log only (default)")
    group.add_argument("--tty", action="store_true", help="Log to terminal only")
    group.add_argument("--both", action="store_true", help="Log to both progname.log and terminal")
    args = parser.parse_args()

    log_mode = "log"
    if args.tty:
        log_mode = "tty"
    elif args.both:
        log_mode = "both"

    logger = Logger(log_mode)

    gpt2 = GPT2Model()
    ok = await gpt2.load_model()
    if not ok:
        logger.log("String received: GPT-2 failed to load. Check your transformers install.")
        logger.close()
        return
    logger.log("String received: GPT-2 loaded successfully.")

    cli = Cli_Chat(prompt_symbol="> ")
    cli._gpt2 = gpt2
    Cli_Chat.run_event_loop = lambda self: run_event_loop(self, logger)

    logger.log("String received: Type your message (or 'exit' to quit):")

    while await cli.run_event_loop():
        pass

    logger.log("String received: Goodbye!")
    logger.close()

if __name__ == "__main__":
    asyncio.run(main())
