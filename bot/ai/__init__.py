"""
AI Integration Module - Main integration for all AI-powered game features.
"""

from typing import Dict, List, Optional
from .llm_client import ai_client
from .game_master import ai_game_master, AIGameMaster
from .task_generator import ai_task_generator, AITaskGenerator
from .voting_analyzer import ai_voting_analyzer, AIVotingAnalyzer
from .chaos_events import ai_chaos_events, AIChaosEvents, ChaosEvent

import logging

logger = logging.getLogger(__name__)


class AIGameEngine:
    """
    Main AI game engine that orchestrates all AI-powered features.
    """

    def __init__(self):
        logger.debug("Initializing AIGameEngine")
        self.llm_client = ai_client
        self.game_master = ai_game_master
        self.task_generator = ai_task_generator
        self.voting_analyzer = ai_voting_analyzer
        self.chaos_events = ai_chaos_events

        # AI feature flags
        self.features_enabled = {
            "ai_narrative": True,
            "ai_tasks": True,
            "ai_voting_analysis": True,
            "ai_chaos_events": True,
            "ai_personas": True,
            "ai_reports": True,
        }

    async def initialize_game_with_ai(self, session_id: int, player_count: int) -> str:
        """Initialize a game with full AI integration."""
        logger.info(
            f"initialize_game_with_ai called with session_id={session_id}, player_count={player_count}"
        )
        if not self.features_enabled["ai_narrative"]:
            return "🎮 **Game Started**\n\nWelcome to the Impostor Game!"

        # Generate AI game introduction
        intro = await self.game_master.initialize_game(session_id, player_count)

        logger.info(f"AI Game Engine initialized game {session_id}")

        return intro

    async def assign_ai_personas(
        self, session_id: int, player_ids: List[int]
    ) -> Dict[int, str]:
        """Assign AI-generated personas to players."""
        logger.debug(
            f"assign_ai_personas called with session_id={session_id}, player_ids={player_ids}"
        )
        if not self.features_enabled["ai_personas"]:
            return {}

        return await self.game_master.assign_player_personas(session_id, player_ids)

    async def generate_ai_task(self, session_id: int, player_id: int, role: str) -> str:
        """Generate an AI-powered task for a player."""
        logger.debug(
            f"generate_ai_task called with session_id={session_id}, player_id={player_id}, role={role}"
        )
        if not self.features_enabled["ai_tasks"]:
            return "Complete your assigned tasks to help the crew."

        task_data = await self.task_generator.generate_task(session_id, player_id, role)
        return task_data["description"]

    async def analyze_voting_with_ai(
        self, session_id: int, vote_results: Dict, round_number: int
    ) -> str:
        """Analyze voting behavior with AI."""
        logger.debug(
            f"analyze_voting_with_ai called with session_id={session_id}, vote_results={vote_results}, round_number={round_number}"
        )
        if not self.features_enabled["ai_voting_analysis"]:
            return ""

        return await self.voting_analyzer.analyze_voting_round(
            session_id, vote_results, round_number
        )

    async def check_chaos_events(self, session_id: int) -> List[ChaosEvent]:
        """Check for AI-generated chaos events."""
        logger.debug(f"check_chaos_events called with session_id={session_id}")
        if not self.features_enabled["ai_chaos_events"]:
            return []

        return await self.chaos_events.check_for_chaos_events(session_id)

    async def generate_player_report(
        self, session_id: int, player_id: int, game_result: Dict
    ) -> str:
        """Generate AI-powered player report."""
        logger.debug(
            f"generate_player_report called with session_id={session_id}, player_id={player_id}, game_result={game_result}"
        )
        if not self.features_enabled["ai_reports"]:
            return f"Game completed. Result: {game_result.get('result', 'Unknown')}"

        return await self.game_master.generate_player_report(
            session_id, player_id, game_result
        )

    async def conclude_game_with_ai(self, session_id: int, game_result: Dict) -> str:
        """Conclude game with AI-generated narrative."""
        logger.debug(
            f"conclude_game_with_ai called with session_id={session_id}, game_result={game_result}"
        )
        if not self.features_enabled["ai_narrative"]:
            return "🎮 **Game Over**\n\nThanks for playing!"

        return await self.game_master.conclude_game(session_id, game_result)

    async def generate_world_lore(self) -> str:
        """Generate AI worldbuilding lore."""
        logger.debug("generate_world_lore called")
        if not self.features_enabled["ai_narrative"]:
            return "📚 **Station Log**\n\nWelcome to the space station."

        return await self.game_master.generate_world_lore()

    def track_player_behavior(
        self, session_id: int, player_id: int, action_type: str, action_data: Dict
    ):
        """Track player behavior for AI analysis."""
        logger.debug(
            f"track_player_behavior called with session_id={session_id}, player_id={player_id}, action_type={action_type}, action_data={action_data}"
        )
        self.voting_analyzer.track_player_behavior(
            session_id, player_id, action_type, action_data
        )

    def get_suspicion_score(self, session_id: int, player_id: int) -> int:
        """Get AI-calculated suspicion score for a player."""
        logger.debug(
            f"get_suspicion_score called with session_id={session_id}, player_id={player_id}"
        )
        return self.voting_analyzer.get_suspicion_score(session_id, player_id)

    async def generate_suspicion_leaderboard(self, session_id: int) -> str:
        """Generate AI-powered suspicion leaderboard."""
        logger.debug(
            f"generate_suspicion_leaderboard called with session_id={session_id}"
        )
        return await self.voting_analyzer.generate_suspicion_leaderboard(session_id)

    def get_ai_stats(self, session_id: int) -> Dict:
        """Get comprehensive AI statistics for a session."""
        logger.debug(f"get_ai_stats called with session_id={session_id}")
        stats = {
            "game_master": self.game_master.get_game_stats(session_id),
            "task_stats": self.task_generator.get_task_progress(
                session_id, 0
            ),  # Placeholder
            "voting_analysis": len(
                self.voting_analyzer.get_analysis_history(session_id)
            ),
            "chaos_events": self.chaos_events.get_chaos_stats(session_id),
        }

        return stats

    def enable_feature(self, feature_name: str):
        """Enable a specific AI feature."""
        logger.debug(f"enable_feature called with feature_name={feature_name}")
        if feature_name in self.features_enabled:
            self.features_enabled[feature_name] = True
            logger.info(f"Enabled AI feature: {feature_name}")

    def disable_feature(self, feature_name: str):
        """Disable a specific AI feature."""
        logger.debug(f"disable_feature called with feature_name={feature_name}")
        if feature_name in self.features_enabled:
            self.features_enabled[feature_name] = False
            logger.info(f"Disabled AI feature: {feature_name}")

    def get_enabled_features(self) -> List[str]:
        """Get list of enabled AI features."""
        logger.debug("get_enabled_features called")
        return [
            feature for feature, enabled in self.features_enabled.items() if enabled
        ]

    def cleanup_session(self, session_id: int):
        """Clean up all AI data for a session."""
        logger.debug(f"cleanup_session called with session_id={session_id}")
        self.game_master._cleanup_game(session_id)
        self.task_generator.cleanup_session_tasks(session_id)
        self.voting_analyzer.cleanup_session_analysis(session_id)
        self.chaos_events.cleanup_session_events(session_id)

        logger.info(f"Cleaned up all AI data for session {session_id}")


# Global AI game engine instance
ai_game_engine = AIGameEngine()
