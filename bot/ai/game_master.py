"""
AI Game Master - Dynamic narrative generation and game flow management.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from bot.ai.llm_client import ai_client
from bot.database import SessionLocal
from bot.database.models import GameSession, PlayerGameLink, DiscussionLog

logger = logging.getLogger(__name__)


class AIGameMaster:
    """AI-powered game master that generates dynamic narratives and manages game flow."""

    def __init__(self):
        self.current_games = {}  # Track active games
        self.game_history = []  # Store game events for lore generation
        self.station_names = [
            "Nebula Prime",
            "Stellar Outpost",
            "Void Station",
            "Cosmic Hub",
            "Quantum Nexus",
            "Stellar Gateway",
            "Void Frontier",
            "Nebula Station",
            "Cosmic Outpost",
            "Quantum Hub",
            "Stellar Nexus",
            "Void Gateway",
        ]

        # Game themes and settings
        self.themes = {
            "standard": "space station",
            "horror": "abandoned research facility",
            "cyberpunk": "corporate orbital platform",
            "military": "classified military base",
            "scientific": "research laboratory",
        }

    async def start_game_session(
        self, game_id: str, players: List[Dict], game_type: str = "standard"
    ) -> Dict[str, Any]:
        """Initialize a new game session with AI-generated narrative."""
        try:
            # Generate unique station name
            station_name = self._get_random_station_name()

            # Generate dramatic opening narrative
            narrative = await ai_client.generate_game_narrative(
                game_type=game_type,
                player_count=len(players),
                theme=self.themes.get(game_type, "space station"),
            )

            # Generate player personas
            player_personas = {}
            for player in players:
                persona = await ai_client.generate_player_persona(
                    player_name=player["name"],
                    role="crewmate",  # Will be updated when roles are assigned
                )
                player_personas[player["id"]] = persona

            # Create game session
            session = {
                "game_id": game_id,
                "station_name": station_name,
                "narrative": narrative,
                "players": players,
                "player_personas": player_personas,
                "game_type": game_type,
                "start_time": datetime.now(),
                "events": [],
                "rounds": [],
                "chaos_events": [],
            }

            self.current_games[game_id] = session

            # Log game start
            self._log_game_event(
                game_id,
                "game_started",
                {
                    "station": station_name,
                    "player_count": len(players),
                    "game_type": game_type,
                },
            )

            return session

        except Exception as e:
            logger.error(f"Failed to start AI game session: {e}")
            return self._get_fallback_session(game_id, players, game_type)

    async def assign_roles_with_narrative(
        self, game_id: str, roles: Dict[int, str]
    ) -> str:
        """Generate narrative for role assignment."""
        try:
            session = self.current_games.get(game_id)
            if not session:
                return "Roles have been assigned. Good luck, crew!"

            # Update player personas with roles
            for player_id, role in roles.items():
                if player_id in session["player_personas"]:
                    persona = session["player_personas"][player_id]
                    persona["role"] = role

                    # Generate role-specific narrative
                    role_narrative = await ai_client.generate_response(
                        f"Generate a brief, dramatic narrative for {persona['name']} discovering they are a {role}",
                        model_type="narrative",
                        max_tokens=80,
                    )
                    persona["role_revelation"] = role_narrative

            # Generate overall role assignment narrative
            impostor_count = sum(1 for role in roles.values() if role == "impostor")
            crew_count = len(roles) - impostor_count

            narrative = await ai_client.generate_response(
                f"Create a dramatic narrative for role assignment in a game with {crew_count} crewmates and {impostor_count} impostors",
                model_type="narrative",
                max_tokens=120,
            )

            return f"🎭 **Role Assignment**\n\n{narrative}"

        except Exception as e:
            logger.error(f"Failed to generate role assignment narrative: {e}")
            return "🎭 **Roles Assigned**\n\nThe crew has received their assignments. Trust no one."

    async def generate_round_narrative(
        self,
        game_id: str,
        round_number: int,
        alive_players: List[str],
        dead_players: List[str],
    ) -> str:
        """Generate narrative for the start of a new round."""
        try:
            session = self.current_games.get(game_id)
            if not session:
                return f"Round {round_number} begins!"

            # Log round start
            self._log_game_event(
                game_id,
                "round_started",
                {
                    "round": round_number,
                    "alive_count": len(alive_players),
                    "dead_count": len(dead_players),
                },
            )

            # Generate round narrative
            prompt = f"""Create a dramatic narrative for round {round_number} of an impostor game:
Alive players: {len(alive_players)}
Dead players: {len(dead_players)}
Station: {session['station_name']}

Make it suspenseful and engaging."""

            narrative = await ai_client.generate_response(
                prompt, model_type="narrative", max_tokens=100
            )

            return f"🔄 **Round {round_number}**\n\n{narrative}"

        except Exception as e:
            logger.error(f"Failed to generate round narrative: {e}")
            return f"🔄 **Round {round_number}**\n\nThe tension builds as the crew continues their mission."

    async def generate_voting_narrative(
        self,
        game_id: str,
        votes: Dict[str, str],
        ejected_player: str,
        round_number: int,
    ) -> str:
        """Generate narrative for voting results."""
        try:
            session = self.current_games.get(game_id)
            if not session:
                return f"Voting complete. {ejected_player} was ejected."

            # Generate AI analysis of voting behavior
            analysis = await ai_client.analyze_voting_behavior(
                votes=votes, ejected_player=ejected_player, round_number=round_number
            )

            # Generate dramatic narrative
            prompt = f"""Create a dramatic narrative for the voting results:
Ejected: {ejected_player}
Round: {round_number}
Station: {session['station_name']}

Make it cinematic and emotional."""

            narrative = await ai_client.generate_response(
                prompt, model_type="narrative", max_tokens=120
            )

            # Log voting event
            self._log_game_event(
                game_id,
                "player_ejected",
                {
                    "ejected_player": ejected_player,
                    "round": round_number,
                    "votes": votes,
                },
            )

            return (
                f"🗳️ **Voting Results**\n\n{narrative}\n\n🤔 **AI Analysis**\n{analysis}"
            )

        except Exception as e:
            logger.error(f"Failed to generate voting narrative: {e}")
            return f"🗳️ **Voting Complete**\n\n{ejected_player} has been ejected from the station."

    async def generate_chaos_event(
        self, game_id: str, trigger: str = "random"
    ) -> Optional[Dict[str, str]]:
        """Generate a random chaos event for the game."""
        try:
            session = self.current_games.get(game_id)
            if not session:
                return None

            # Determine if chaos event should trigger
            if trigger == "random":
                # 15% chance of chaos event per round
                import random

                if random.random() > 0.15:
                    return None

            # Generate chaos event
            game_state = (
                f"Round {len(session['rounds']) + 1}, {len(session['players'])} players"
            )
            chaos_event = await ai_client.generate_chaos_event(
                game_state=game_state, player_count=len(session["players"])
            )

            # Log chaos event
            self._log_game_event(game_id, "chaos_event", chaos_event)
            session["chaos_events"].append(chaos_event)

            return chaos_event

        except Exception as e:
            logger.error(f"Failed to generate chaos event: {e}")
            return None

    async def end_game_session(
        self, game_id: str, winner: str, game_stats: Dict[str, Any]
    ) -> str:
        """Generate dramatic conclusion for the game."""
        try:
            session = self.current_games.get(game_id)
            if not session:
                return f"Game ended. {winner} wins!"

            # Generate game conclusion narrative
            prompt = f"""Create a dramatic conclusion for an impostor game:
Winner: {winner}
Game duration: {len(session['rounds'])} rounds
Station: {session['station_name']}
Chaos events: {len(session['chaos_events'])}

Make it epic and memorable."""

            conclusion = await ai_client.generate_response(
                prompt, model_type="narrative", max_tokens=150
            )

            # Generate player reports
            player_reports = {}
            for player in session["players"]:
                player_stats = game_stats.get(str(player["id"]), {})
                report = await ai_client.generate_player_report(
                    player_name=player["name"],
                    game_stats=player_stats,
                    role=player_stats.get("role", "unknown"),
                    won=player_stats.get("won", False),
                )
                player_reports[player["id"]] = report

            # Log game end
            self._log_game_event(
                game_id,
                "game_ended",
                {
                    "winner": winner,
                    "duration": len(session["rounds"]),
                    "chaos_events": len(session["chaos_events"]),
                },
            )

            # Store in history
            game_summary = {
                "game_id": game_id,
                "station": session["station_name"],
                "winner": winner,
                "duration": len(session["rounds"]),
                "player_count": len(session["players"]),
                "chaos_events": len(session["chaos_events"]),
                "timestamp": datetime.now(),
            }
            self.game_history.append(game_summary)

            # Clean up current game
            del self.current_games[game_id]

            return f"🪐 **Mission Complete**\n\n{conclusion}"

        except Exception as e:
            logger.error(f"Failed to generate game conclusion: {e}")
            return f"🪐 **Game Over**\n\n{winner} has emerged victorious!"

    async def generate_world_lore(self, season: int = 1) -> str:
        """Generate evolving world lore based on game history."""
        try:
            if not self.game_history:
                return "The station awaits its first mission..."

            lore = await ai_client.generate_world_lore(
                game_history=self.game_history, season=season
            )

            return f"📚 **Station Archives - Season {season}**\n\n{lore}"

        except Exception as e:
            logger.error(f"Failed to generate world lore: {e}")
            return "The station's history is shrouded in mystery..."

    def get_player_persona(self, game_id: str, player_id: int) -> Optional[Dict]:
        """Get the AI-generated persona for a player."""
        session = self.current_games.get(game_id)
        if session and player_id in session["player_personas"]:
            return session["player_personas"][player_id]
        return None

    def _get_random_station_name(self) -> str:
        """Get a random space station name."""
        import random

        return random.choice(self.station_names)

    def _log_game_event(self, game_id: str, event_type: str, data: Dict):
        """Log a game event for history tracking."""
        event = {
            "game_id": game_id,
            "event_type": event_type,
            "data": data,
            "timestamp": datetime.now(),
        }

        session = self.current_games.get(game_id)
        if session:
            session["events"].append(event)

    def _get_fallback_session(
        self, game_id: str, players: List[Dict], game_type: str
    ) -> Dict[str, Any]:
        """Create a fallback session when AI is unavailable."""
        return {
            "game_id": game_id,
            "station_name": self._get_random_station_name(),
            "narrative": "The crew prepares for another mission aboard the space station.",
            "players": players,
            "player_personas": {},
            "game_type": game_type,
            "start_time": datetime.now(),
            "events": [],
            "rounds": [],
            "chaos_events": [],
        }


# Global AI Game Master instance
ai_game_master = AIGameMaster()
