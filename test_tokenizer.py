"""
Test script to demonstrate the tokenizer warnings.
"""
import sys

from transformers import pipeline, AutoTokenizer

def test_default_pipeline():
    """Test default pipeline without pad token configuration"""
    print("Testing default pipeline:")
    try:
        generator = pipeline('text-generation', model='gpt2')
        output = generator("Hello, GPT-2! ", max_length=30)
        print("Output:", output)
    except Exception as e:
        print(f"Error: {e}")

def test_with_tokenizer():
    """Test pipeline with properly configured tokenizer"""
    print("\nTesting with configured tokenizer:")
    try:
        # Initialize tokenizer
        tokenizer = AutoTokenizer.from_pretrained('gpt2')
        # Set pad_token to eos_token
        tokenizer.pad_token = tokenizer.eos_token
        # Create pipeline with configured tokenizer
        generator = pipeline('text-generation', model='gpt2', tokenizer=tokenizer)
        output = generator("Hello, GPT-2! ", max_length=30)
        print("Output:", output)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("Starting tokenizer tests...")
    
    if "--with-tokenizer" in sys.argv:
        test_with_tokenizer()
    elif "--default" in sys.argv:
        test_default_pipeline()
    else:
        test_default_pipeline()
        test_with_tokenizer()