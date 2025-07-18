# This will handle the AI integration, including generating roleplay, analyzing behavior, and simulating expressions.
from bot.ai.llm_client import ai_client


class AIManager:
    async def generate_bio(self, player_name, role):
        prompt = f"Create a unique character bio for {player_name} who is a {role} in a high-stakes deception game."
        return await ai_client.generate_response(prompt, model_type="creative")

    async def analyze_expression(self, expression):
        prompt = f"Analyze the following expression from a player in a deception game: {expression}"
        return await ai_client.generate_response(prompt, model_type="reasoning")

    async def generate_alibi(self, player_name):
        prompt = f"Generate a plausible alibi for {player_name} who is trying to avoid suspicion."
        return await ai_client.generate_response(prompt, model_type="creative")
