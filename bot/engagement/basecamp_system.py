"""
Player Basecamp System - Personal rooms with trophies and customization.
"""

import json
from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime
from bot.database import SessionLocal
from bot.database.models import Player
import logging

logger = logging.getLogger(__name__)


class RoomTheme(Enum):
    DEFAULT = "default"
    DARK = "dark"
    NEON = "neon"
    NATURE = "nature"
    SPACE = "space"
    RETRO = "retro"


class TrophyType(Enum):
    FIRST_WIN = "first_win"
    WIN_STREAK = "win_streak"
    TASK_MASTER = "task_master"
    IMPOSTOR_MASTER = "impostor_master"
    VOTING_ACCURATE = "voting_accurate"
    MVP = "mvp"
    SEASONAL = "seasonal"
    SPECIAL = "special"


class Trophy:
    """Represents a trophy/achievement."""
    
    def __init__(self, trophy_type: TrophyType, name: str, description: str, 
                 emoji: str, rarity: str, unlocked_at: Optional[datetime] = None):
        self.trophy_type = trophy_type
        self.name = name
        self.description = description
        self.emoji = emoji
        self.rarity = rarity  # common, rare, epic, legendary
        self.unlocked_at = unlocked_at or datetime.now()
    
    def to_dict(self):
        return {
            "type": self.trophy_type.value,
            "name": self.name,
            "description": self.description,
            "emoji": self.emoji,
            "rarity": self.rarity,
            "unlocked_at": self.unlocked_at.isoformat() if self.unlocked_at else None
        }


class BasecampSystem:
    """Manages player basecamps and personal rooms."""
    
    def __init__(self):
        # Available themes with their styling
        self.themes = {
            RoomTheme.DEFAULT: {
                "name": "🏠 Cozy Cabin",
                "description": "A warm, welcoming space",
                "emoji": "🏠",
                "color": "#4A90E2"
            },
            RoomTheme.DARK: {
                "name": "🖤 Shadow Den",
                "description": "Dark and mysterious",
                "emoji": "🖤",
                "color": "#2C3E50"
            },
            RoomTheme.NEON: {
                "name": "💫 Cyber Lounge",
                "description": "Bright neon lights",
                "emoji": "💫",
                "color": "#E74C3C"
            },
            RoomTheme.NATURE: {
                "name": "🌿 Garden Retreat",
                "description": "Peaceful and natural",
                "emoji": "🌿",
                "color": "#27AE60"
            },
            RoomTheme.SPACE: {
                "name": "🚀 Cosmic Station",
                "description": "Out of this world",
                "emoji": "🚀",
                "color": "#9B59B6"
            },
            RoomTheme.RETRO: {
                "name": "📺 Vintage Vibes",
                "description": "Old school cool",
                "emoji": "📺",
                "color": "#F39C12"
            }
        }
        
        # Available trophies
        self.trophy_definitions = {
            TrophyType.FIRST_WIN: Trophy(
                TrophyType.FIRST_WIN, "First Victory", "Win your first game", "🏆", "common"
            ),
            TrophyType.WIN_STREAK: Trophy(
                TrophyType.WIN_STREAK, "Hot Streak", "Win 5 games in a row", "🔥", "rare"
            ),
            TrophyType.TASK_MASTER: Trophy(
                TrophyType.TASK_MASTER, "Task Master", "Complete 50 tasks", "🔧", "epic"
            ),
            TrophyType.IMPOSTOR_MASTER: Trophy(
                TrophyType.IMPOSTOR_MASTER, "Impostor Master", "Win 10 times as impostor", "🎭", "epic"
            ),
            TrophyType.VOTING_ACCURATE: Trophy(
                TrophyType.VOTING_ACCURATE, "Sharp Eye", "Vote correctly 20 times", "👁️", "rare"
            ),
            TrophyType.MVP: Trophy(
                TrophyType.MVP, "Most Valuable Player", "Be MVP in a game", "⭐", "legendary"
            ),
            TrophyType.SEASONAL: Trophy(
                TrophyType.SEASONAL, "Seasonal Champion", "Win during special events", "🎃", "rare"
            ),
            TrophyType.SPECIAL: Trophy(
                TrophyType.SPECIAL, "Special Achievement", "Unlock special content", "💎", "legendary"
            )
        }
    
    def get_player_basecamp(self, player_id: int) -> Dict[str, Any]:
        """Get a player's complete basecamp data."""
        db = SessionLocal()
        try:
            player = db.query(Player).filter(Player.id == player_id).first()
            if not player:
                return {}
            
            # Get player's trophies (stored as JSON in database)
            trophies = []
            if hasattr(player, 'trophies') and player.trophies:
                try:
                    trophy_data = json.loads(player.trophies)
                    for trophy_info in trophy_data:
                        trophy = Trophy(
                            TrophyType(trophy_info["type"]),
                            trophy_info["name"],
                            trophy_info["description"],
                            trophy_info["emoji"],
                            trophy_info["rarity"],
                            datetime.fromisoformat(trophy_info["unlocked_at"]) if trophy_info.get("unlocked_at") else None
                        )
                        trophies.append(trophy)
                except (json.JSONDecodeError, KeyError):
                    trophies = []
            
            # Get room theme (default if not set)
            theme_name = getattr(player, 'room_theme', RoomTheme.DEFAULT.value)
            try:
                theme = RoomTheme(theme_name)
            except ValueError:
                theme = RoomTheme.DEFAULT
            
            theme_info = self.themes[theme]
            
            return {
                "player": {
                    "name": player.name,
                    "title": player.title,
                    "xp": player.xp,
                    "wins": player.wins,
                    "losses": player.losses,
                    "tasks_done": player.tasks_done
                },
                "room": {
                    "theme": theme.value,
                    "theme_info": theme_info,
                    "layout": getattr(player, 'room_layout', 'default')
                },
                "trophies": [trophy.to_dict() for trophy in trophies],
                "stats": {
                    "total_trophies": len(trophies),
                    "rare_trophies": len([t for t in trophies if t.rarity in ["rare", "epic", "legendary"]]),
                    "win_rate": player.wins / (player.wins + player.losses) if (player.wins + player.losses) > 0 else 0
                }
            }
            
        finally:
            db.close()
    
    def unlock_trophy(self, player_id: int, trophy_type: TrophyType, 
                     custom_name: Optional[str] = None) -> Optional[Trophy]:
        """Unlock a trophy for a player."""
        if trophy_type not in self.trophy_definitions:
            return None
        
        db = SessionLocal()
        try:
            player = db.query(Player).filter(Player.id == player_id).first()
            if not player:
                return None
            
            # Get existing trophies
            trophies = []
            if hasattr(player, 'trophies') and player.trophies:
                try:
                    trophies = json.loads(player.trophies)
                except json.JSONDecodeError:
                    trophies = []
            
            # Check if already unlocked
            for trophy in trophies:
                if trophy["type"] == trophy_type.value:
                    return None  # Already unlocked
            
            # Create new trophy
            base_trophy = self.trophy_definitions[trophy_type]
            new_trophy = Trophy(
                trophy_type,
                custom_name or base_trophy.name,
                base_trophy.description,
                base_trophy.emoji,
                base_trophy.rarity
            )
            
            # Add to player's trophies
            trophies.append(new_trophy.to_dict())
            
            # Update database
            if hasattr(player, 'trophies'):
                player.trophies = json.dumps(trophies)
            else:
                # If trophies column doesn't exist, we'll need to add it
                logger.warning("Trophies column not found in Player model")
            
            db.commit()
            
            logger.info(f"Player {player_id} unlocked trophy: {new_trophy.name}")
            return new_trophy
            
        except Exception as e:
            logger.error(f"Failed to unlock trophy: {e}")
            db.rollback()
            return None
        finally:
            db.close()
    
    def change_room_theme(self, player_id: int, theme: RoomTheme) -> bool:
        """Change a player's room theme."""
        db = SessionLocal()
        try:
            player = db.query(Player).filter(Player.id == player_id).first()
            if not player:
                return False
            
            # Update theme
            if hasattr(player, 'room_theme'):
                player.room_theme = theme.value
            else:
                # If room_theme column doesn't exist, we'll need to add it
                logger.warning("Room theme column not found in Player model")
                return False
            
            db.commit()
            
            logger.info(f"Player {player_id} changed room theme to: {theme.value}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to change room theme: {e}")
            db.rollback()
            return False
        finally:
            db.close()
    
    def generate_basecamp_display(self, player_id: int) -> str:
        """Generate a beautiful display of the player's basecamp."""
        basecamp = self.get_player_basecamp(player_id)
        if not basecamp:
            return "❌ Basecamp not found."
        
        player = basecamp["player"]
        room = basecamp["room"]
        trophies = basecamp["trophies"]
        stats = basecamp["stats"]
        
        theme_info = room["theme_info"]
        
        # Calculate win rate percentage
        win_rate = stats["win_rate"] * 100
        
        # Trophy display
        trophy_display = ""
        if trophies:
            # Group by rarity
            rarity_groups = {}
            for trophy in trophies:
                rarity = trophy["rarity"]
                if rarity not in rarity_groups:
                    rarity_groups[rarity] = []
                rarity_groups[rarity].append(trophy)
            
            for rarity in ["legendary", "epic", "rare", "common"]:
                if rarity in rarity_groups:
                    trophy_display += f"\n{rarity.title()} Trophies:\n"
                    for trophy in rarity_groups[rarity][:3]:  # Show top 3 per rarity
                        trophy_display += f"  {trophy['emoji']} {trophy['name']}\n"
                    if len(rarity_groups[rarity]) > 3:
                        trophy_display += f"  ... and {len(rarity_groups[rarity]) - 3} more\n"
        else:
            trophy_display = "\n🏆 No trophies yet. Play games to earn them!"
        
        return (
            f"{theme_info['emoji']} **{player['name']}'s {theme_info['name']}**\n\n"
            f"🏷️ **Title:** {player['title']}\n"
            f"✨ **XP:** {player['xp']}\n"
            f"🎮 **Record:** {player['wins']}W/{player['losses']}L ({win_rate:.1f}%)\n"
            f"🔧 **Tasks Completed:** {player['tasks_done']}\n"
            f"🏆 **Trophies:** {stats['total_trophies']} ({stats['rare_trophies']} rare+)\n\n"
            f"**🏠 Room Theme:** {theme_info['name']}\n"
            f"*{theme_info['description']}*\n"
            f"{trophy_display}"
        )
    
    def get_available_themes(self) -> List[Dict]:
        """Get all available room themes."""
        return [
            {
                "id": theme.value,
                "name": info["name"],
                "description": info["description"],
                "emoji": info["emoji"],
                "color": info["color"]
            }
            for theme, info in self.themes.items()
        ]


# Global instance
basecamp_system = BasecampSystem() 