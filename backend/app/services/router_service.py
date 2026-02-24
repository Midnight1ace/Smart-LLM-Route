import os
import json
import numpy as np
from typing import List, Optional, Dict, Any
from sentence_transformers import SentenceTransformer
from app.core.config import get_settings
from app.services.llm_provider import get_llm_provider


class SemanticCache:
    def __init__(self):
        # Using a simple in-memory cache for now as a fallback if Redis is not available
        self.cache: Dict[str, str] = {}
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.embeddings = []
        self.queries = []

    def get(self, query: str, threshold: float = 0.95) -> Optional[str]:
        if not self.queries:
            return None
        
        query_embedding = self.model.encode([query])[0]
        
        # Calculate cosine similarity manually for the cache
        norms = np.linalg.norm(self.embeddings, axis=1) * np.linalg.norm(query_embedding)
        # Avoid division by zero
        norms[norms == 0] = 1e-9
        similarities = np.dot(self.embeddings, query_embedding) / norms
        
        max_idx = np.argmax(similarities)
        if similarities[max_idx] >= threshold:
            return self.cache[self.queries[max_idx]]
        
        return None

    def set(self, query: str, response: str):
        query_embedding = self.model.encode([query])[0]
        self.queries.append(query)
        self.embeddings.append(query_embedding)
        self.cache[query] = response

class RouterService:
    def __init__(self):
        self.cache = SemanticCache()
        self.settings = get_settings()
        self.llm = get_llm_provider()
        
        # Analytics state (in-memory for demo)
        self.total_cost_actual = 0.0
        self.total_cost_theoretical = 0.0 # Cost if all queries were GPT-4o
        self.queries_count = 0
        
        # Layer 1: Semantic Router Setup
        # Note: SemanticRouter initialization removed as it is bypassed in route_query
        pass

    async def _get_slm_intent(self, query: str) -> Dict[str, Any]:
        """Layer 2: Use a small model to classify intent and complexity."""
        system_prompt = (
            "You are an intent classifier. Output ONLY valid JSON. "
            "Format: {\"complexity\": 1-5, \"specialization\": \"coding\"|\"math\"|\"creative\"|\"general\"}"
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Classify this query: {query}"}
        ]
        
        try:
            response_text = await self.llm.complete(model="gpt-4o-mini", messages=messages, temperature=0)
            return json.loads(response_text)
        except Exception:
            return {"complexity": 3, "specialization": "general"}

    def _update_stats(self, model: str, query: str, response: str):
        # Very rough token estimation (4 chars per token)
        input_tokens = len(query) // 4
        output_tokens = len(response) // 4
        
        actual_cost = self.llm.estimate_cost(model, input_tokens, output_tokens)
        theoretical_cost = self.llm.estimate_cost("gpt-4o", input_tokens, output_tokens)
        
        self.total_cost_actual += actual_cost
        self.total_cost_theoretical += theoretical_cost
        self.queries_count += 1

    async def route_query(self, query: str, model_hint: Optional[str] = None) -> str:
        # Layer 0: Semantic Cache
        cached_response = self.cache.get(query)
        if cached_response:
            return f"[CACHE HIT] {cached_response}"
        
        # Layer 1: Custom Semantic Routing (Replacing unreliable SemanticRouter)
        query_embedding = self.cache.model.encode([query])[0]
        
        routes = {
            "coding": [
                "how do I write a for loop in python",
                "debug this javascript code",
                "explain recursion in rust",
                "how to implement a linked list",
                "what is a decorator in python"
            ],
            "math": [
                "solve this integral",
                "what is the derivative of sin(x)",
                "calculate the area of a circle",
                "what is the square root of 144",
                "explain the pythagorean theorem"
            ]
        }
        
        route_choice = "default"
        max_sim = 0.0
        
        for name, utterances in routes.items():
            u_embeddings = self.cache.model.encode(utterances)
            # Cosine similarity
            sims = np.dot(u_embeddings, query_embedding) / (np.linalg.norm(u_embeddings, axis=1) * np.linalg.norm(query_embedding))
            sim = np.max(sims)
            if sim > max_sim:
                max_sim = sim
                if sim > 0.5: # Threshold for routing
                    route_choice = name

        target_model = "gpt-4o-mini" # Default
        route_label = "DEFAULT"

        if route_choice == "coding":
            target_model = "gpt-4o"
            route_label = "CODING"
        elif route_choice == "math":
            target_model = "gpt-4o-mini"
            route_label = "MATH"
        else:
            # Layer 2: Intent Classification (SLM)
            intent = await self._get_slm_intent(query)
            if intent["complexity"] >= 4:
                target_model = "gpt-4o"
                route_label = "HIGH_COMPLEXITY"
            else:
                target_model = "gpt-4o-mini"
                route_label = "LOW_COMPLEXITY"

        try:
            # Execution with Scale-Up Fallback
            response = await self.llm.complete(model=target_model, messages=[{"role": "user", "content": query}])
            
            # Simple validation: if coding query return is too short, maybe it failed
            if route_label == "CODING" and len(response) < 20 and target_model == "gpt-4o-mini":
                 # Fallback/Escalate to Premium
                 response = await self.llm.complete(model="gpt-4o", messages=[{"role": "user", "content": query}])
                 target_model = "gpt-4o"
                 route_label = f"{route_label}_ESCALATED"

        except Exception:
            # If target model fails, try premium as ultimate fallback
            if target_model != "gpt-4o":
                response = await self.llm.complete(model="gpt-4o", messages=[{"role": "user", "content": query}])
                target_model = "gpt-4o"
                route_label = f"{route_label}_FALLBACK"
            else:
                raise

        self._update_stats(target_model, query, response)
        self.cache.set(query, response)
        
        savings = self.total_cost_theoretical - self.total_cost_actual
        return f"[ROUTED: {route_label} -> {target_model}] [SAVINGS: ${savings:.4f}] {response}"

router_instance = RouterService()

def get_router_service():
    return router_instance
