import asyncio
import sys
import os

# Add current directory to path at the very beginning to avoid package collisions
sys.path.insert(0, os.getcwd())

import app
print(f"DEBUG: app package location: {app.__file__}")

from app.services.router_service import RouterService
from app.services.llm_provider import LLMProvider
from unittest.mock import AsyncMock, MagicMock

async def test_routing():
    print("🚀 Starting Smart LLM Router Verification...")
    
    # Mock LLM Provider
    mock_llm = MagicMock()
    mock_llm.complete = AsyncMock(return_value="Mocked response content.")
    mock_llm.estimate_cost = MagicMock(return_value=0.0001)
    
    # Initialize Router with mocked bits if possible, or just test high level
    router = RouterService()
    router.llm = mock_llm # Inject mock
    
    # Test Case 1: Coding (Layer 1)
    print("\nTest 1: Coding Route")
    res1 = await router.route_query("how to write a for loop in python")
    print(f"Result: {res1}")
    assert "CODING" in res1
    
    # Test Case 2: Math (Layer 1)
    print("\nTest 2: Math Route")
    res2 = await router.route_query("solve integral of x^2")
    print(f"Result: {res2}")
    assert "MATH" in res2
    
    # Test Case 3: General/SLM (Layer 2)
    print("\nTest 3: General Query (High Complexity)")
    mock_llm.complete.side_effect = ["{\"complexity\": 5, \"specialization\": \"general\"}", "High complexity answer."]
    res3 = await router.route_query("Explain quantum entanglement in detail.")
    print(f"Result: {res3}")
    assert "HIGH_COMPLEXITY" in res3
    
    # Test Case 4: Cache (Layer 0)
    print("\nTest 4: Cache Hit")
    res4 = await router.route_query("how to write a for loop in python")
    print(f"Result: {res4}")
    assert "[CACHE HIT]" in res4
    
    # Test Case 5: Stats
    print("\nTest 5: Stats Endpoint")
    print(f"Total Actual Cost: {router.total_cost_actual}")
    print(f"Total Queries: {router.queries_count}")
    assert router.queries_count >= 3
    
    print("\n✅ Verification Complete! All logic layers functioning correctly.")

if __name__ == "__main__":
    asyncio.run(test_routing())
