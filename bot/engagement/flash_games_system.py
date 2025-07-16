"""
Flash Games System - FOMO-driven limited events with exclusive rewards.
"""

import random
from typing import Dict, List, Optional, Tuple
from enum import Enum
from datetime import datetime, timedelta
from bot.database import SessionLocal
from bot.database.models import Player
import logging

logger = logging.getLogger(__name__)


class FlashEventType(Enum):
    FRIDAY_NIGHT = "friday_night"
    WEEKEND_WARRIOR = "weekend_warrior"
    HOLIDAY_SPECIAL = "holiday_special"
    SEASONAL_EVENT = "seasonal_event"
    MYSTERY_HOUR = "mystery_hour"


class FlashGame:
    """Represents a flash game event."""

    def __init__(
        self,
        event_id: str,
        name: str,
        description: str,
        event_type: FlashEventType,
        start_time: datetime,
        duration_hours: int,
        max_players: int,
        rewards: Dict,
    ):
        self.event_id = event_id
        self.name = name
        self.description = description
        self.event_type = event_type
        self.start_time = start_time
        self.end_time = start_time + timedelta(hours=duration_hours)
        self.duration_hours = duration_hours
        self.max_players = max_players
        self.rewards = rewards
        self.emoji = self._get_event_emoji(event_type)
        self.status = "upcoming"  # upcoming, active, finished

    def _get_event_emoji(self, event_type: FlashEventType) -> str:
        """Get emoji for event type."""
        emojis = {
            FlashEventType.FRIDAY_NIGHT: "🌙",
            FlashEventType.WEEKEND_WARRIOR: "⚔️",
            FlashEventType.HOLIDAY_SPECIAL: "🎉",
            FlashEventType.SEASONAL_EVENT: "🍂",
            FlashEventType.MYSTERY_HOUR: "❓",
        }
        return emojis.get(event_type, "⚡")

    def is_active(self) -> bool:
        """Check if the event is currently active."""
        now = datetime.now()
        return self.start_time <= now <= self.end_time

    def is_upcoming(self) -> bool:
        """Check if the event is upcoming."""
        return datetime.now() < self.start_time

    def time_until_start(self) -> Optional[timedelta]:
        """Get time until event starts."""
        if self.is_upcoming():
            return self.start_time - datetime.now()
        return None

    def time_remaining(self) -> Optional[timedelta]:
        """Get time remaining in event."""
        if self.is_active():
            return self.end_time - datetime.now()
        return None


class FlashGamesSystem:
    """Manages flash game events and FOMO mechanics."""

    def __init__(self):
        # Track active flash events
        self.active_events = {}

        # Track event participants: {event_id: {player_id: join_time}}
        self.event_participants = {}

        # Track event results: {event_id: {player_id: result}}
        self.event_results = {}

        # Event templates
        self.event_templates = {
            "friday_night": {
                "name": "🌙 Friday Night Fever",
                "description": "Special Friday night games with exclusive rewards!",
                "event_type": FlashEventType.FRIDAY_NIGHT,
                "duration_hours": 4,
                "max_players": 50,
                "rewards": {
                    "xp_bonus": 2.0,  # 2x XP
                    "exclusive_badge": "friday_night_fever",
                    "exclusive_title": "🌙 Night Owl",
                    "crate_boost": 1.5,  # 1.5x crate drop rate
                },
            },
            "weekend_warrior": {
                "name": "⚔️ Weekend Warrior",
                "description": "Intense weekend battles with legendary rewards!",
                "event_type": FlashEventType.WEEKEND_WARRIOR,
                "duration_hours": 48,
                "max_players": 100,
                "rewards": {
                    "xp_bonus": 1.5,
                    "exclusive_badge": "weekend_warrior",
                    "exclusive_title": "⚔️ Warrior",
                    "crate_boost": 1.2,
                },
            },
            "holiday_special": {
                "name": "🎉 Holiday Special",
                "description": "Celebrate with special holiday-themed games!",
                "event_type": FlashEventType.HOLIDAY_SPECIAL,
                "duration_hours": 24,
                "max_players": 75,
                "rewards": {
                    "xp_bonus": 2.5,
                    "exclusive_badge": "holiday_cheer",
                    "exclusive_title": "🎉 Celebrator",
                    "crate_boost": 2.0,
                },
            },
            "mystery_hour": {
                "name": "❓ Mystery Hour",
                "description": "Random events with unknown rewards!",
                "event_type": FlashEventType.MYSTERY_HOUR,
                "duration_hours": 1,
                "max_players": 25,
                "rewards": {
                    "xp_bonus": 3.0,
                    "exclusive_badge": "mystery_solver",
                    "exclusive_title": "❓ Enigma",
                    "crate_boost": 3.0,
                },
            },
        }

    def schedule_friday_night_event(self) -> Optional[FlashGame]:
        """Schedule a Friday night flash event."""
        now = datetime.now()

        # Check if it's Friday
        if now.weekday() != 4:  # Friday is 4
            return None

        # Check if event already exists for this Friday
        friday_start = now.replace(hour=20, minute=0, second=0, microsecond=0)  # 8 PM

        event_id = f"friday_night_{friday_start.strftime('%Y%m%d')}"

        if event_id in self.active_events:
            return self.active_events[event_id]

        template = self.event_templates["friday_night"]

        flash_game = FlashGame(
            event_id=event_id,
            name=template["name"],
            description=template["description"],
            event_type=template["event_type"],
            start_time=friday_start,
            duration_hours=template["duration_hours"],
            max_players=template["max_players"],
            rewards=template["rewards"],
        )

        self.active_events[event_id] = flash_game
        self.event_participants[event_id] = {}
        self.event_results[event_id] = {}

        logger.info(f"Scheduled Friday night event: {event_id}")
        return flash_game

    def schedule_mystery_hour_event(self) -> Optional[FlashGame]:
        """Schedule a mystery hour event (random timing)."""
        now = datetime.now()

        # Random start time within next 24 hours
        random_hour = random.randint(1, 23)
        start_time = now + timedelta(hours=random_hour)
        start_time = start_time.replace(minute=0, second=0, microsecond=0)

        event_id = f"mystery_hour_{start_time.strftime('%Y%m%d_%H')}"

        if event_id in self.active_events:
            return self.active_events[event_id]

        template = self.event_templates["mystery_hour"]

        flash_game = FlashGame(
            event_id=event_id,
            name=template["name"],
            description=template["description"],
            event_type=template["event_type"],
            start_time=start_time,
            duration_hours=template["duration_hours"],
            max_players=template["max_players"],
            rewards=template["rewards"],
        )

        self.active_events[event_id] = flash_game
        self.event_participants[event_id] = {}
        self.event_results[event_id] = {}

        logger.info(f"Scheduled mystery hour event: {event_id}")
        return flash_game

    def join_flash_event(self, player_id: int, event_id: str) -> Tuple[bool, str]:
        """Join a flash event."""
        if event_id not in self.active_events:
            return False, "❌ Event not found."

        event = self.active_events[event_id]

        if not event.is_active():
            return False, "❌ Event is not active."

        if player_id in self.event_participants[event_id]:
            return False, "❌ You're already participating in this event."

        if len(self.event_participants[event_id]) >= event.max_players:
            return False, "❌ Event is full!"

        # Join the event
        self.event_participants[event_id][player_id] = datetime.now()

        logger.info(f"Player {player_id} joined flash event: {event_id}")

        return True, (
            f"🎉 **Joined {event.name}!**\n\n"
            f"📝 {event.description}\n"
            f"⏰ Duration: {event.duration_hours} hours\n"
            f"👥 Participants: {len(self.event_participants[event_id])}/{event.max_players}\n\n"
            f"🎁 **Rewards:**\n"
            f"✨ {event.rewards['xp_bonus']}x XP Bonus\n"
            f"🏆 Exclusive Badge\n"
            f"🏷️ Exclusive Title"
        )

    def get_active_events(self) -> List[FlashGame]:
        """Get all currently active flash events."""
        active = []
        for event in self.active_events.values():
            if event.is_active():
                active.append(event)
        return active

    def get_upcoming_events(self) -> List[FlashGame]:
        """Get all upcoming flash events."""
        upcoming = []
        for event in self.active_events.values():
            if event.is_upcoming():
                upcoming.append(event)
        return upcoming

    def get_event_status(self, event_id: str) -> Optional[Dict]:
        """Get detailed status of an event."""
        if event_id not in self.active_events:
            return None

        event = self.active_events[event_id]
        participants = self.event_participants.get(event_id, {})

        status = {
            "event": event,
            "participant_count": len(participants),
            "slots_remaining": event.max_players - len(participants),
            "is_active": event.is_active(),
            "is_upcoming": event.is_upcoming(),
            "time_until_start": event.time_until_start(),
            "time_remaining": event.time_remaining(),
        }

        return status

    def generate_flash_events_display(self) -> str:
        """Generate a display of all flash events."""
        active_events = self.get_active_events()
        upcoming_events = self.get_upcoming_events()

        if not active_events and not upcoming_events:
            return "⚡ **No Flash Events**\n\nCheck back later for special events!"

        display = "⚡ **Flash Events**\n\n"

        # Active events
        if active_events:
            display += "🎯 **Active Events:**\n"
            for event in active_events:
                participants = self.event_participants.get(event.event_id, {})
                time_remaining = event.time_remaining()

                display += (
                    f"{event.emoji} **{event.name}**\n"
                    f"📝 {event.description}\n"
                    f"👥 {len(participants)}/{event.max_players} players\n"
                    f"⏰ {time_remaining.seconds // 3600}h {(time_remaining.seconds % 3600) // 60}m remaining\n\n"
                )

        # Upcoming events
        if upcoming_events:
            display += "📅 **Upcoming Events:**\n"
            for event in upcoming_events:
                time_until = event.time_until_start()

                display += (
                    f"{event.emoji} **{event.name}**\n"
                    f"📝 {event.description}\n"
                    f"⏰ Starts in {time_until.seconds // 3600}h {(time_until.seconds % 3600) // 60}m\n\n"
                )

        return display

    def apply_event_rewards(self, player_id: int, event_id: str, base_xp: int) -> int:
        """Apply event rewards to a player."""
        if event_id not in self.active_events:
            return base_xp

        event = self.active_events[event_id]

        if player_id not in self.event_participants.get(event_id, {}):
            return base_xp

        # Apply XP bonus
        bonus_xp = int(base_xp * event.rewards["xp_bonus"])

        # Store result
        if event_id not in self.event_results:
            self.event_results[event_id] = {}

        self.event_results[event_id][player_id] = {
            "base_xp": base_xp,
            "bonus_xp": bonus_xp,
            "total_xp": bonus_xp,
            "rewards_earned": event.rewards,
        }

        logger.info(f"Applied event rewards to player {player_id}: +{bonus_xp} XP")

        return bonus_xp

    def cleanup_expired_events(self):
        """Clean up expired flash events."""
        now = datetime.now()
        expired_events = []

        for event_id, event in self.active_events.items():
            if event.end_time < now:
                expired_events.append(event_id)

        for event_id in expired_events:
            del self.active_events[event_id]
            # Keep participants and results for analytics

        if expired_events:
            logger.info(f"Cleaned up {len(expired_events)} expired flash events")

    def get_event_leaderboard(self, event_id: str) -> List[Dict]:
        """Get leaderboard for a specific event."""
        if event_id not in self.event_results:
            return []

        results = self.event_results[event_id]
        leaderboard = []

        for player_id, result in results.items():
            db = SessionLocal()
            try:
                player = db.query(Player).filter(Player.id == player_id).first()
                if player:
                    leaderboard.append(
                        {
                            "player_name": player.name,
                            "total_xp": result["total_xp"],
                            "base_xp": result["base_xp"],
                            "bonus_xp": result["bonus_xp"],
                        }
                    )
            finally:
                db.close()

        # Sort by total XP
        leaderboard.sort(key=lambda x: x["total_xp"], reverse=True)

        return leaderboard


# Global instance
flash_games_system = FlashGamesSystem()
