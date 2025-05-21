import asyncio
from models.gpt2.gpt2_model import GPT2Model

async def main():
    # 1. Instantiate the GPT-2 wrapper
    model = GPT2Model()
    
    # 2. Load / initialize the model
    ok = await model.load_model()          # or await model.initialize()
    if not ok:
        print("❌ GPT-2 failed to load. Check your transformers install.")
        return

    print("✅ GPT-2 loaded successfully.")

    # 3. Use the pipeline to generate text
    #    `model.generator` is a HuggingFace pipeline callable
    output = model.generator("Hello, GPT-2! ", max_length=30)
    print("Generation output:", output)

if __name__ == "__main__":
    asyncio.run(main())
