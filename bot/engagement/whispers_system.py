"""
Whispers & Secrets System - Private communication mechanics.
"""

import random
from typing import Dict, List, Optional, Tuple
from enum import Enum
from datetime import datetime, timedelta
from bot.database import SessionLocal
from bot.database.models import Player, DiscussionLog
import logging

logger = logging.getLogger(__name__)


class WhisperType(Enum):
    ALLY_REQUEST = "ally_request"
    SECRET_INFO = "secret_info"
    DECEPTION = "deception"
    WARNING = "warning"
    CONFESSION = "confession"


class WhisperSystem:
    """Manages private whispers and secrets between players."""
    
    def __init__(self):
        self.active_whispers = {}  # session_id -> {player_id -> [whispers]}
        self.whisper_cooldowns = {}  # player_id -> last_whisper_time
        self.secret_pools = {
            WhisperType.ALLY_REQUEST: [
                "I trust you. Let's work together to find the impostor.",
                "I have a feeling about [player]. What do you think?",
                "Can we share information? I think I know something.",
                "Let's form an alliance. I'll watch your back."
            ],
            WhisperType.SECRET_INFO: [
                "I saw [player] near the vent when the body was found.",
                "[player] was acting suspicious during the last meeting.",
                "I completed a task and [player] was there too.",
                "I noticed [player] didn't do any tasks this round."
            ],
            WhisperType.DECEPTION: [
                "I'm definitely crewmate. I can prove it.",
                "I have a special role that can help us win.",
                "I know who the impostor is, but I need backup.",
                "Trust me, I'm on your side completely."
            ],
            WhisperType.WARNING: [
                "Be careful around [player]. They seem suspicious.",
                "I don't trust [player]. Watch out for them.",
                "Something feels off about [player].",
                "I think [player] might be the impostor."
            ],
            WhisperType.CONFESSION: [
                "I made a mistake in the last vote. I'm sorry.",
                "I was wrong about [player]. I feel bad.",
                "I should have listened to you earlier.",
                "I'm not sure what to do anymore."
            ]
        }
    
    def send_whisper(self, session_id: int, from_player_id: int, to_player_id: int, 
                    whisper_type: WhisperType, custom_message: str = None) -> Tuple[bool, str]:
        """Send a whisper from one player to another."""
        # Check cooldown
        if not self._check_whisper_cooldown(from_player_id):
            return False, "⏰ You can only send whispers every 30 seconds."
        
        # Check if both players are in the same session
        if not self._validate_players_in_session(session_id, [from_player_id, to_player_id]):
            return False, "❌ One or both players are not in this game session."
        
        # Generate or use custom message
        if custom_message:
            message = custom_message
        else:
            message = self._generate_whisper_message(whisper_type, from_player_id, to_player_id)
        
        # Store whisper
        if session_id not in self.active_whispers:
            self.active_whispers[session_id] = {}
        
        if to_player_id not in self.active_whispers[session_id]:
            self.active_whispers[session_id][to_player_id] = []
        
        whisper_data = {
            "from_player_id": from_player_id,
            "type": whisper_type.value,
            "message": message,
            "timestamp": datetime.now(),
            "read": False
        }
        
        self.active_whispers[session_id][to_player_id].append(whisper_data)
        
        # Set cooldown
        self.whisper_cooldowns[from_player_id] = datetime.now()
        
        # Log to database
        self._log_whisper_to_db(session_id, from_player_id, to_player_id, whisper_type, message)
        
        logger.info(f"Whisper sent: {from_player_id} -> {to_player_id} ({whisper_type.value})")
        
        return True, f"💬 Whisper sent to player {to_player_id}"
    
    def get_player_whispers(self, session_id: int, player_id: int) -> List[Dict]:
        """Get all whispers for a player in a session."""
        if session_id not in self.active_whispers:
            return []
        
        return self.active_whispers[session_id].get(player_id, [])
    
    def mark_whisper_read(self, session_id: int, player_id: int, whisper_index: int):
        """Mark a whisper as read."""
        if (session_id in self.active_whispers and 
            player_id in self.active_whispers[session_id] and
            whisper_index < len(self.active_whispers[session_id][player_id])):
            
            self.active_whispers[session_id][player_id][whisper_index]["read"] = True
    
    def get_unread_whisper_count(self, session_id: int, player_id: int) -> int:
        """Get count of unread whispers for a player."""
        whispers = self.get_player_whispers(session_id, player_id)
        return sum(1 for w in whispers if not w.get("read", False))
    
    def generate_whisper_menu(self, session_id: int, player_id: int) -> str:
        """Generate a menu for sending whispers."""
        # Get other players in the session
        other_players = self._get_other_players_in_session(session_id, player_id)
        
        if not other_players:
            return "❌ No other players available for whispers."
        
        menu = "💬 **Whisper Menu**\n\n"
        menu += "**Available Players:**\n"
        
        for other_player in other_players:
            unread_count = self.get_unread_whisper_count(session_id, other_player["id"])
            unread_indicator = f" ({unread_count} new)" if unread_count > 0 else ""
            menu += f"• {other_player['name']}{unread_indicator}\n"
        
        menu += "\n**Whisper Types:**\n"
        menu += "• 🤝 Ally Request - Form alliances\n"
        menu += "• 🔍 Secret Info - Share observations\n"
        menu += "• 🎭 Deception - Mislead others\n"
        menu += "• ⚠️ Warning - Alert about suspicions\n"
        menu += "• 😔 Confession - Admit mistakes\n"
        
        return menu
    
    def _check_whisper_cooldown(self, player_id: int) -> bool:
        """Check if player can send another whisper."""
        if player_id not in self.whisper_cooldowns:
            return True
        
        last_whisper = self.whisper_cooldowns[player_id]
        cooldown_duration = timedelta(seconds=30)
        
        return datetime.now() - last_whisper >= cooldown_duration
    
    def _validate_players_in_session(self, session_id: int, player_ids: List[int]) -> bool:
        """Check if players are in the same session."""
        db = SessionLocal()
        try:
            from bot.database.models import PlayerGameLink
            
            for player_id in player_ids:
                link = db.query(PlayerGameLink).filter(
                    PlayerGameLink.session_id == session_id,
                    PlayerGameLink.player_id == player_id,
                    PlayerGameLink.left_at.is_(None)
                ).first()
                
                if not link:
                    return False
            
            return True
        finally:
            db.close()
    
    def _generate_whisper_message(self, whisper_type: WhisperType, from_player_id: int, to_player_id: int) -> str:
        """Generate a random whisper message of the specified type."""
        messages = self.secret_pools[whisper_type]
        base_message = random.choice(messages)
        
        # Replace placeholders with actual player names
        db = SessionLocal()
        try:
            from_player = db.query(Player).filter(Player.id == from_player_id).first()
            to_player = db.query(Player).filter(Player.id == to_player_id).first()
            
            if from_player and to_player:
                message = base_message.replace("[player]", to_player.name)
                return message
            
            return base_message
        finally:
            db.close()
    
    def _get_other_players_in_session(self, session_id: int, player_id: int) -> List[Dict]:
        """Get other players in the same session."""
        db = SessionLocal()
        try:
            from bot.database.models import PlayerGameLink
            
            links = db.query(PlayerGameLink).filter(
                PlayerGameLink.session_id == session_id,
                PlayerGameLink.player_id != player_id,
                PlayerGameLink.left_at.is_(None)
            ).all()
            
            players = []
            for link in links:
                player = db.query(Player).filter(Player.id == link.player_id).first()
                if player:
                    players.append({
                        "id": player.id,
                        "name": player.name
                    })
            
            return players
        finally:
            db.close()
    
    def _log_whisper_to_db(self, session_id: int, from_player_id: int, to_player_id: int, 
                          whisper_type: WhisperType, message: str):
        """Log whisper to database for analytics."""
        db = SessionLocal()
        try:
            whisper_log = DiscussionLog(
                session_id=session_id,
                player_id=from_player_id,
                message=f"WHISPER to {to_player_id}: {message}",
                phase="whisper",
                whisper_target=to_player_id
            )
            db.add(whisper_log)
            db.commit()
        except Exception as e:
            logger.error(f"Failed to log whisper: {e}")
            db.rollback()
        finally:
            db.close()
    
    def cleanup_session_whispers(self, session_id: int):
        """Clean up whispers for a finished session."""
        if session_id in self.active_whispers:
            del self.active_whispers[session_id]
            logger.info(f"Cleaned up whispers for session {session_id}")


# Global instance
whisper_system = WhisperSystem() 