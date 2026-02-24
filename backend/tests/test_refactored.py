import httpx
import asyncio

async def test_routing():
    url = "http://localhost:8000/v1/chat/completions"
    payload = {
        "model": "gpt-4o",
        "messages": [{"role": "user", "content": "how to write a loop in python"}]
    }
    
    print(f"Testing routing with query: {payload['messages'][0]['content']}...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=30.0)
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.json()['choices'][0]['message']['content'][:200]}...")
    except Exception as e:
        print(f"Error during test: {e}")

if __name__ == "__main__":
    asyncio.run(test_routing())
