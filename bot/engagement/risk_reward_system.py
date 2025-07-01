"""
Risk-Reward Mode System - XP wagering for high-stakes gameplay.
"""

import random
from typing import Dict, List, Optional, Tuple
from enum import Enum
from datetime import datetime, timedelta
from bot.database import SessionLocal
from bot.database.models import Player
import logging

logger = logging.getLogger(__name__)


class WagerType(Enum):
    CONSERVATIVE = "conservative"  # 10% XP, 1.5x multiplier
    MODERATE = "moderate"         # 25% XP, 2x multiplier
    AGGRESSIVE = "aggressive"     # 50% XP, 3x multiplier
    ALL_IN = "all_in"            # 100% XP, 5x multiplier


class RiskRewardSystem:
    """Manages risk-reward mode with XP wagering."""
    
    def __init__(self):
        # Wager configurations
        self.wager_configs = {
            WagerType.CONSERVATIVE: {
                "name": "Conservative",
                "emoji": "🛡️",
                "xp_percentage": 0.10,
                "multiplier": 1.5,
                "description": "Safe bet, small gains"
            },
            WagerType.MODERATE: {
                "name": "Moderate",
                "emoji": "⚖️",
                "xp_percentage": 0.25,
                "multiplier": 2.0,
                "description": "Balanced risk and reward"
            },
            WagerType.AGGRESSIVE: {
                "name": "Aggressive",
                "emoji": "🔥",
                "xp_percentage": 0.50,
                "multiplier": 3.0,
                "description": "High risk, high reward"
            },
            WagerType.ALL_IN: {
                "name": "All In",
                "emoji": "💀",
                "xp_percentage": 1.0,
                "multiplier": 5.0,
                "description": "Everything on the line"
            }
        }
        
        # Track active wagers: {player_id: WagerInfo}
        self.active_wagers = {}
    
    def place_wager(self, player_id: int, wager_type: WagerType) -> Tuple[bool, str]:
        """Place a wager for a player."""
        if player_id in self.active_wagers:
            return False, "❌ You already have an active wager!"
        
        db = SessionLocal()
        try:
            player = db.query(Player).filter(Player.id == player_id).first()
            if not player:
                return False, "❌ Player not found."
            
            config = self.wager_configs[wager_type]
            wager_amount = int(player.xp * config["xp_percentage"])
            
            if wager_amount <= 0:
                return False, "❌ You need more XP to place a wager."
            
            # Store wager info
            wager_info = {
                "player_id": player_id,
                "wager_type": wager_type,
                "wager_amount": wager_amount,
                "multiplier": config["multiplier"],
                "placed_at": datetime.now(),
                "game_id": None  # Will be set when game starts
            }
            
            self.active_wagers[player_id] = wager_info
            
            logger.info(f"Player {player_id} placed {wager_type.value} wager: {wager_amount} XP")
            
            return True, (
                f"{config['emoji']} **{config['name']} Wager Placed!**\n\n"
                f"💰 **Wagered:** {wager_amount} XP\n"
                f"📈 **Multiplier:** {config['multiplier']}x\n"
                f"🎯 **Potential Win:** {wager_amount * config['multiplier']} XP\n\n"
                f"*{config['description']}*"
            )
            
        except Exception as e:
            logger.error(f"Failed to place wager: {e}")
            return False, "❌ Failed to place wager."
        finally:
            db.close()
    
    def cancel_wager(self, player_id: int) -> Tuple[bool, str]:
        """Cancel a player's active wager."""
        if player_id not in self.active_wagers:
            return False, "❌ No active wager found."
        
        wager_info = self.active_wagers[player_id]
        
        # Check if game has already started
        if wager_info.get("game_id"):
            return False, "❌ Cannot cancel wager after game has started."
        
        # Remove wager
        del self.active_wagers[player_id]
        
        logger.info(f"Player {player_id} cancelled wager")
        
        return True, "✅ Wager cancelled successfully."
    
    def get_wager_info(self, player_id: int) -> Optional[Dict]:
        """Get information about a player's active wager."""
        if player_id not in self.active_wagers:
            return None
        
        wager_info = self.active_wagers[player_id]
        config = self.wager_configs[wager_info["wager_type"]]
        
        return {
            "wager_type": wager_info["wager_type"].value,
            "wager_amount": wager_info["wager_amount"],
            "multiplier": wager_info["multiplier"],
            "potential_win": wager_info["wager_amount"] * wager_info["multiplier"],
            "config": config,
            "placed_at": wager_info["placed_at"]
        }
    
    def assign_wager_to_game(self, player_id: int, game_id: str):
        """Assign a wager to a specific game."""
        if player_id in self.active_wagers:
            self.active_wagers[player_id]["game_id"] = game_id
    
    def resolve_wager(self, player_id: int, game_result: Dict) -> Tuple[bool, str]:
        """Resolve a wager based on game result."""
        if player_id not in self.active_wagers:
            return False, "❌ No active wager found."
        
        wager_info = self.active_wagers[player_id]
        config = self.wager_configs[wager_info["wager_type"]]
        
        db = SessionLocal()
        try:
            player = db.query(Player).filter(Player.id == player_id).first()
            if not player:
                return False, "❌ Player not found."
            
            won = game_result.get("won", False)
            wager_amount = wager_info["wager_amount"]
            multiplier = wager_info["multiplier"]
            
            if won:
                # Player wins - apply multiplier
                xp_gained = int(wager_amount * multiplier)
                player.xp += xp_gained
                
                result_message = (
                    f"🎉 **Wager Won!**\n\n"
                    f"{config['emoji']} **{config['name']} Wager**\n"
                    f"💰 **Wagered:** {wager_amount} XP\n"
                    f"📈 **Multiplier:** {multiplier}x\n"
                    f"✨ **Won:** +{xp_gained} XP\n\n"
                    f"*{config['description']}*"
                )
                
                logger.info(f"Player {player_id} won wager: +{xp_gained} XP")
                
            else:
                # Player loses - deduct wager amount
                player.xp -= wager_amount
                
                result_message = (
                    f"💀 **Wager Lost!**\n\n"
                    f"{config['emoji']} **{config['name']} Wager**\n"
                    f"💰 **Lost:** -{wager_amount} XP\n"
                    f"📉 **Multiplier:** {multiplier}x\n\n"
                    f"*{config['description']}*"
                )
                
                logger.info(f"Player {player_id} lost wager: -{wager_amount} XP")
            
            # Ensure XP doesn't go negative
            if player.xp < 0:
                player.xp = 0
            
            db.commit()
            
            # Remove wager
            del self.active_wagers[player_id]
            
            return True, result_message
            
        except Exception as e:
            logger.error(f"Failed to resolve wager: {e}")
            db.rollback()
            return False, "❌ Failed to resolve wager."
        finally:
            db.close()
    
    def get_wager_display(self, player_id: int) -> str:
        """Get a display of the player's current wager."""
        wager_info = self.get_wager_info(player_id)
        if not wager_info:
            return "❌ No active wager."
        
        config = wager_info["config"]
        
        return (
            f"{config['emoji']} **Active Wager**\n\n"
            f"🎯 **Type:** {config['name']}\n"
            f"💰 **Amount:** {wager_info['wager_amount']} XP\n"
            f"📈 **Multiplier:** {wager_info['multiplier']}x\n"
            f"✨ **Potential Win:** {wager_info['potential_win']} XP\n\n"
            f"*{config['description']}*"
        )
    
    def get_wager_stats(self, player_id: int) -> Dict:
        """Get wager statistics for a player."""
        # This would need to be implemented with a separate table
        # For now, return basic stats
        return {
            "total_wagers": 0,
            "wagers_won": 0,
            "wagers_lost": 0,
            "total_xp_wagered": 0,
            "total_xp_won": 0,
            "win_rate": 0.0
        }
    
    def get_leaderboard_wagers(self) -> List[Dict]:
        """Get leaderboard of players with active wagers."""
        wager_players = []
        
        for player_id, wager_info in self.active_wagers.items():
            db = SessionLocal()
            try:
                player = db.query(Player).filter(Player.id == player_id).first()
                if player:
                    config = self.wager_configs[wager_info["wager_type"]]
                    wager_players.append({
                        "player_name": player.name,
                        "wager_type": wager_info["wager_type"].value,
                        "wager_amount": wager_info["wager_amount"],
                        "potential_win": wager_info["wager_amount"] * wager_info["multiplier"],
                        "emoji": config["emoji"]
                    })
            finally:
                db.close()
        
        # Sort by potential win amount
        wager_players.sort(key=lambda x: x["potential_win"], reverse=True)
        
        return wager_players


# Global instance
risk_reward_system = RiskRewardSystem() 