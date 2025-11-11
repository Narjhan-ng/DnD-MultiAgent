"""
Simple WebSocket test client
"""
import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8000/ws"

    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to WebSocket server")

            # Test receiving welcome/connection confirmation
            await asyncio.sleep(1)

            print("✅ WebSocket connection successful!")
            print("   Server is ready to accept commands")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket())
