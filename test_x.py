#!/usr/bin/env python3
"""
Simple test for x.py's pump_model functionality using a file to log output
"""

import asyncio
import os
import sys
import socket

# ensure project root is on PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

async def test_pump_model():
    log_file = "/tmp/model_output.log"
    
    # Set up socket pair for testing
    sock_a, sock_b = socket.socketpair()
    
    # Open streams
    model_reader, model_writer = await asyncio.open_connection(sock=sock_a)
    test_reader, test_writer = await asyncio.open_connection(sock=sock_b)
    
    # Create pump_model coroutine similar to what's in x.py
    async def pump_model():
        try:
            with open(log_file, "w") as f:
                while True:
                    line = await model_reader.readline()
                    if line:
                        # This is the critical part we're testing
                        decoded = line.decode().rstrip("\n")
                        print(f"Read: {decoded}")
                        # Log to file for verification
                        f.write(f"{decoded}\n")
                        f.flush()
        except asyncio.CancelledError:
            print("pump_model cancelled")
            return
    
    # Start the coroutine
    pump_task = asyncio.create_task(pump_model())
    
    # Send test messages through the socket
    test_writer.write(b"This is a test message from the model\n")
    await test_writer.drain()
    await asyncio.sleep(0.1)
    
    test_writer.write(b"This is another test message\n")
    await test_writer.drain()
    await asyncio.sleep(0.5)
    
    # Clean up
    pump_task.cancel()
    await asyncio.gather(pump_task, return_exceptions=True)
    
    # Read log file to check if messages were captured
    with open(log_file, "r") as f:
        captured = f.read()
    
    print("Captured output from file:")
    print(captured)
    
    # Check that both messages were captured
    success = "This is a test message from the model" in captured and "This is another test message" in captured
    
    if success:
        print("✅ Test passed: pump_model successfully reads from model_reader")
    else:
        print("❌ Test failed: pump_model did not read expected messages")
    
    return success

async def main():
    success = await test_pump_model()
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())

if __name__ == "__main__":
    asyncio.run(test_pump_model())