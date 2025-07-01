"""
AI LLM Client - Centralized AI integration for all game features
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from huggingface_hub import InferenceClient
import os

logger = logging.getLogger(__name__)


class GameLLMClient:
    """Centralized LLM client for all AI-powered game features."""
    
    def __init__(self):
        self.hf_token = os.getenv("HF_API_KEY")
        if not self.hf_token:
            logger.warning("HF_API_KEY not found - AI features will be disabled")
            self.enabled = False
        else:
            self.enabled = True
        
        # Initialize different models for different use cases
        self.models = {
            "narrative": "mistralai/Mistral-7B-Instruct-v0.1",  # Story generation
            "reasoning": "tiiuae/falcon-7b-instruct",           # Vote analysis, logic
            "creative": "openchat/openchat-3.5-1210",          # Personas, creative tasks
            "fast": "meta-llama/Llama-2-7b-chat-hf"            # Quick responses
        }
        
        self.clients = {}
        self._initialize_clients()
        
        # Cache for common responses to avoid repeated API calls
        self.response_cache = {}
        self.cache_ttl = 3600  # 1 hour cache
    
    def _initialize_clients(self):
        """Initialize Hugging Face clients for different models."""
        if not self.enabled:
            return
            
        try:
            for model_type, model_name in self.models.items():
                self.clients[model_type] = InferenceClient(
                    model=model_name,
                    token=self.hf_token
                )
            logger.info("AI clients initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize AI clients: {e}")
            self.enabled = False
    
    async def generate_response(self, 
                              prompt: str, 
                              model_type: str = "narrative",
                              max_tokens: int = 200,
                              temperature: float = 0.7,
                              cache_key: Optional[str] = None) -> str:
        """Generate AI response with caching and error handling."""
        if not self.enabled:
            return self._get_fallback_response(prompt, model_type)
        
        # Check cache first
        if cache_key and cache_key in self.response_cache:
            cached = self.response_cache[cache_key]
            if datetime.now().timestamp() - cached["timestamp"] < self.cache_ttl:
                return cached["response"]
        
        try:
            # Format prompt based on model type
            formatted_prompt = self._format_prompt(prompt, model_type)
            
            # Get response from appropriate model
            client = self.clients.get(model_type, self.clients["narrative"])
            
            response = client.text_generation(
                formatted_prompt,
                max_new_tokens=max_tokens,
                temperature=temperature,
                do_sample=True,
                return_full_text=False
            )
            
            # Clean and validate response
            cleaned_response = self._clean_response(response)
            
            # Cache if requested
            if cache_key:
                self.response_cache[cache_key] = {
                    "response": cleaned_response,
                    "timestamp": datetime.now().timestamp()
                }
            
            return cleaned_response
            
        except Exception as e:
            logger.error(f"AI generation failed: {e}")
            return self._get_fallback_response(prompt, model_type)
    
    def _format_prompt(self, prompt: str, model_type: str) -> str:
        """Format prompt based on model type and use case."""
        if model_type == "narrative":
            return f"""<s>[INST] You are a creative game master for a space-themed impostor game. 
Generate engaging, dramatic narrative content. Keep responses under 150 words.
Context: {prompt} [/INST]"""
        
        elif model_type == "reasoning":
            return f"""<s>[INST] You are an AI detective analyzing player behavior in a social deduction game.
Provide logical, analytical insights. Be concise and observant.
Analysis request: {prompt} [/INST]"""
        
        elif model_type == "creative":
            return f"""<s>[INST] You are a creative AI generating unique game content, personas, and tasks.
Be imaginative, fun, and engaging. Keep responses under 100 words.
Request: {prompt} [/INST]"""
        
        else:  # fast
            return f"""<s>[INST] Provide a quick, helpful response for a game scenario.
Be concise and direct.
Request: {prompt} [/INST]"""
    
    def _clean_response(self, response: str) -> str:
        """Clean and validate AI response."""
        if not response:
            return "AI response unavailable"
        
        # Remove any model-specific formatting
        cleaned = response.strip()
        cleaned = cleaned.replace("<s>", "").replace("</s>", "")
        cleaned = cleaned.replace("[INST]", "").replace("[/INST]", "")
        
        # Limit length
        if len(cleaned) > 500:
            cleaned = cleaned[:497] + "..."
        
        return cleaned
    
    def _get_fallback_response(self, prompt: str, model_type: str) -> str:
        """Provide fallback responses when AI is disabled."""
        fallbacks = {
            "narrative": [
                "The space station hums with tension as the crew prepares for another mission.",
                "In the depths of space, trust is the rarest commodity.",
                "The void between stars holds secrets that could destroy them all."
            ],
            "reasoning": [
                "The voting patterns suggest careful consideration.",
                "Player behavior indicates strategic thinking.",
                "The group dynamics reveal interesting social dynamics."
            ],
            "creative": [
                "A mysterious task awaits completion.",
                "The crew faces a challenging mission.",
                "An opportunity for heroism presents itself."
            ],
            "fast": [
                "Processing...",
                "Analyzing...",
                "Computing..."
            ]
        }
        
        import random
        return random.choice(fallbacks.get(model_type, fallbacks["fast"]))
    
    # Specialized AI methods for different game features
    
    async def generate_game_narrative(self, 
                                    game_type: str = "standard",
                                    player_count: int = 6,
                                    theme: str = "space station") -> str:
        """Generate dramatic game narrative."""
        prompt = f"""Create a dramatic opening narrative for a {game_type} impostor game on a {theme} with {player_count} players. 
Include suspense, mystery, and urgency. Make it feel like a sci-fi thriller."""
        
        return await self.generate_response(
            prompt, 
            model_type="narrative",
            max_tokens=150,
            temperature=0.8
        )
    
    async def generate_player_persona(self, 
                                    player_name: str,
                                    role: str = "crewmate") -> Dict[str, str]:
        """Generate unique player persona and behavior."""
        prompt = f"""Create a unique character persona for {player_name} who is a {role}.
Include: personality traits, background story, and secret behavior goal.
Format as JSON with keys: name, personality, background, secret_goal"""
        
        response = await self.generate_response(
            prompt,
            model_type="creative",
            max_tokens=200,
            temperature=0.9
        )
        
        try:
            # Try to parse JSON response
            persona = json.loads(response)
            return persona
        except:
            # Fallback if JSON parsing fails
            return {
                "name": player_name,
                "personality": "Mysterious and cautious",
                "background": "A veteran space explorer",
                "secret_goal": "Prove their innocence at all costs"
            }
    
    async def generate_dynamic_task(self, 
                                  role: str,
                                  player_name: str,
                                  difficulty: str = "medium") -> str:
        """Generate dynamic task for player."""
        prompt = f"""Create a unique task for {player_name} who is a {role}.
Difficulty: {difficulty}
Make it engaging and thematic. For impostors, create sabotage or deception tasks."""
        
        return await self.generate_response(
            prompt,
            model_type="creative",
            max_tokens=100,
            temperature=0.7
        )
    
    async def analyze_voting_behavior(self, 
                                    votes: Dict[str, str],
                                    ejected_player: str,
                                    round_number: int) -> str:
        """Analyze voting patterns and provide insights."""
        prompt = f"""Analyze this voting round in an impostor game:
Votes: {votes}
Ejected: {ejected_player}
Round: {round_number}

Provide 2-3 insights about voting patterns, player behavior, or strategic implications."""
        
        return await self.generate_response(
            prompt,
            model_type="reasoning",
            max_tokens=150,
            temperature=0.6
        )
    
    async def generate_player_report(self, 
                                   player_name: str,
                                   game_stats: Dict[str, Any],
                                   role: str,
                                   won: bool) -> str:
        """Generate personalized player report."""
        prompt = f"""Create a personalized game report for {player_name}:
Role: {role}
Won: {won}
Stats: {game_stats}

Make it dramatic, personalized, and include a unique title and tip for improvement."""
        
        return await self.generate_response(
            prompt,
            model_type="narrative",
            max_tokens=200,
            temperature=0.8
        )
    
    async def generate_chaos_event(self, 
                                 game_state: str,
                                 player_count: int) -> Dict[str, str]:
        """Generate random chaos event for the game."""
        prompt = f"""Generate a chaos event for an impostor game:
Current state: {game_state}
Players: {player_count}

Create an event that adds drama and unpredictability.
Format as JSON with keys: event_name, description, effect"""
        
        response = await self.generate_response(
            prompt,
            model_type="creative",
            max_tokens=150,
            temperature=0.9
        )
        
        try:
            return json.loads(response)
        except:
            return {
                "event_name": "System Malfunction",
                "description": "Communications are temporarily disrupted",
                "effect": "Players cannot vote this round"
            }
    
    async def generate_world_lore(self, 
                                game_history: List[Dict],
                                season: int = 1) -> str:
        """Generate evolving world lore based on game history."""
        prompt = f"""Based on this game history, generate evolving world lore:
Games played: {len(game_history)}
Season: {season}
Recent events: {game_history[-5:] if game_history else 'None'}

Create a mysterious, evolving narrative that connects the games."""
        
        return await self.generate_response(
            prompt,
            model_type="narrative",
            max_tokens=200,
            temperature=0.8
        )


# Global AI client instance
ai_client = GameLLMClient() 