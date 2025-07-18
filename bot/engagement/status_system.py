"""
Status System - Limited-Edition Titles & Social Status with Scarcity
"""

import random
from typing import Dict, List, Optional, Set
from enum import Enum
from datetime import datetime, timedelta
from bot.database import SessionLocal
from bot.database.models import Player
import logging

logger = logging.getLogger(__name__)


class TitleRarity(Enum):
    """Title rarity levels with different scarcity."""

    COMMON = "common"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"
    MYTHIC = "mythic"
    LIMITED = "limited"


class StatusSystem:
    """Manages player titles, status, and social hierarchy."""

    def __init__(self):
        # Limited edition titles (only 10 players can hold each)
        self.limited_titles = {
            "Shadow Master": {"max_holders": 10, "expires": None},
            "Ghost Whisperer": {"max_holders": 10, "expires": None},
            "Void Walker": {"max_holders": 10, "expires": None},
        }

        # Regular titles with XP requirements
        self.regular_titles = {
            "Rookie": {"xp_required": 0, "rarity": TitleRarity.COMMON},
            "Detective": {"xp_required": 250, "rarity": TitleRarity.COMMON},
            "Sleuth": {"xp_required": 1000, "rarity": TitleRarity.RARE},
            "Master Detective": {"xp_required": 2000, "rarity": TitleRarity.EPIC},
        }

        # Title holders tracking
        self.title_holders: Dict[str, Set[int]] = {}
        self._load_title_holders()

    def _load_title_holders(self):
        """Load current title holders from database."""
        db = SessionLocal()
        try:
            players = db.query(Player).all()
            for player in players:
                if player.title and player.title not in self.title_holders:
                    self.title_holders[player.title] = set()
                if player.title:
                    self.title_holders[player.title].add(player.id)
        except Exception as e:
            logger.error(f"Failed to load title holders: {e}")
        finally:
            db.close()

    def get_available_titles(self, player_id: int) -> List[str]:
        """Get all titles available to a player."""
        db = SessionLocal()
        try:
            player = db.query(Player).filter(Player.id == player_id).first()
            if not player:
                return ["Rookie"]

            available = ["Rookie"]

            # Check regular titles based on XP
            for title, config in self.regular_titles.items():
                if player.xp >= config["xp_required"]:
                    available.append(title)

            # Check limited titles (if slots available)
            for title, config in self.limited_titles.items():
                current_holders = len(self.title_holders.get(title, set()))
                if current_holders < config["max_holders"]:
                    available.append(title)

            return available

        except Exception as e:
            logger.error(f"Failed to get available titles for player {player_id}: {e}")
            return ["Rookie"]
        finally:
            db.close()

    def assign_title(self, player_id: int, title: str) -> bool:
        """Assign a title to a player if available."""
        db = SessionLocal()
        try:
            player = db.query(Player).filter(Player.id == player_id).first()
            if not player:
                return False

            available_titles = self.get_available_titles(player_id)
            if title not in available_titles:
                return False

            # Remove from old title holders
            if player.title and player.title in self.title_holders:
                self.title_holders[player.title].discard(player_id)

            # Assign new title
            player.title = title

            # Add to new title holders
            if title not in self.title_holders:
                self.title_holders[title] = set()
            self.title_holders[title].add(player_id)

            db.commit()
            logger.info(f"Assigned title '{title}' to player {player_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to assign title to player {player_id}: {e}")
            db.rollback()
            return False
        finally:
            db.close()

    def get_title_info(self, title: str) -> Optional[Dict]:
        """Get information about a specific title."""
        if title in self.regular_titles:
            return {
                "type": "regular",
                "rarity": self.regular_titles[title]["rarity"].value,
                "xp_required": self.regular_titles[title]["xp_required"],
                "current_holders": len(self.title_holders.get(title, set())),
                "max_holders": None,
            }
        elif title in self.limited_titles:
            return {
                "type": "limited",
                "rarity": TitleRarity.LIMITED.value,
                "current_holders": len(self.title_holders.get(title, set())),
                "max_holders": self.limited_titles[title]["max_holders"],
            }
        return None

    def cleanup_expired_seasonal_titles(self):
        """Cleanup expired seasonal/limited titles. (No expiration logic implemented yet.)"""
        logger.debug(
            "cleanup_expired_seasonal_titles called, but no expiration logic implemented."
        )
        # If you add expiration dates to limited_titles, implement removal logic here.
        pass


# Global instance
status_system = StatusSystem()
