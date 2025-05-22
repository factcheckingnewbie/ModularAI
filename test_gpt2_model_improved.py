"""
Test script demonstrating the improved GPT2 model with proper tokenizer configuration.
"""

import asyncio
import logging
from models.gpt2.gpt2_model import GPT2Model

# Set logging level to see warnings
logging.basicConfig(level=logging.INFO)

async def main():
    """Test the improved model implementation"""
    print("Testing improved GPT2 model implementation...")
    
    # 1. Instantiate the GPT-2 wrapper
    model = GPT2Model()
    
    # 2. Load / initialize the model
    ok = await model.load_model()
    if not ok:
        print("❌ GPT-2 failed to load. Check your transformers install or internet connection.")
        return
    
    print("✅ GPT-2 loaded successfully (with properly configured tokenizer).")
    
    # 3. Use the pipeline to generate text
    prompt = "Hello, GPT-2! "
    print(f"Generating text for prompt: '{prompt}'")
    try:
        generated_text = await model.generate_text(prompt, max_length=50)
        print("-" * 40)
        print("Generated text:")
        print(generated_text)
        print("-" * 40)
        print("✅ Text generation successful without tokenizer warnings")
    except Exception as e:
        print(f"❌ Error generating text: {e}")
    
    # 4. Clean up
    await model.shutdown()
    print("Model shutdown complete.")

if __name__ == "__main__":
    asyncio.run(main())