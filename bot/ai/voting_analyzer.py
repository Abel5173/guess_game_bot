"""
AI Voting Analyzer - Intelligent analysis of voting patterns and player behavior.
"""

import random
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging
from bot.ai.llm_client import ai_client
from bot.database import SessionLocal
from bot.database.models import VoteHistory, Player, DiscussionLog

logger = logging.getLogger(__name__)


class AIVotingAnalyzer:
    """AI-powered voting analysis and detective insights."""
    
    def __init__(self):
        self.voting_patterns = {}  # session_id -> {player_id -> patterns}
        self.analysis_history = {}  # session_id -> [analyses]
        self.suspicion_scores = {}  # session_id -> {player_id -> score}
        self.behavior_tracking = {}  # session_id -> {player_id -> behaviors}
        
        # Analysis types
        self.analysis_types = [
            "voting_speed",
            "voting_consistency", 
            "group_behavior",
            "suspicious_patterns",
            "defensive_actions",
            "accusation_patterns"
        ]
    
    async def analyze_voting_round(self, session_id: int, vote_results: Dict, 
                                 round_number: int) -> str:
        """Generate comprehensive AI analysis of a voting round."""
        # Collect voting data
        voting_data = self._collect_voting_data(session_id, round_number)
        
        # Analyze patterns
        patterns = self._analyze_voting_patterns(voting_data, vote_results)
        
        # Generate AI insights
        insights = await self._generate_ai_insights(session_id, patterns, vote_results)
        
        # Update suspicion scores
        self._update_suspicion_scores(session_id, patterns)
        
        # Store analysis
        self._store_analysis(session_id, round_number, insights, patterns)
        
        return insights
    
    async def generate_player_behavior_report(self, session_id: int, player_id: int) -> str:
        """Generate a detailed behavior analysis for a specific player."""
        if session_id not in self.behavior_tracking:
            return "❌ No behavior data available for this session."
        
        if player_id not in self.behavior_tracking[session_id]:
            return "❌ No behavior data available for this player."
        
        behavior_data = self.behavior_tracking[session_id][player_id]
        suspicion_score = self.suspicion_scores.get(session_id, {}).get(player_id, 0)
        
        # Get player name
        db = SessionLocal()
        try:
            player = db.query(Player).filter(Player.id == player_id).first()
            player_name = player.name if player else "Unknown Player"
        finally:
            db.close()
        
        # Generate AI analysis
        analysis_prompt = f"""
Analyze this player's behavior in a space station impostor game:

Player: {player_name}
Voting Speed: {behavior_data.get('avg_vote_time', 'Unknown')} seconds
Vote Consistency: {behavior_data.get('vote_consistency', 'Unknown')}%
Accusations Made: {behavior_data.get('accusations', 0)}
Defensive Actions: {behavior_data.get('defensive_actions', 0)}
Suspicion Score: {suspicion_score}/100

Provide 2-3 sentences of detective-style analysis about this player's behavior.
Focus on suspicious patterns or interesting observations.
"""
        
        analysis = await ai_client.generate_text("reasoning", analysis_prompt, 150)
        
        return f"🔍 **Behavior Analysis: {player_name}**\n\n{analysis}"
    
    async def generate_suspicion_leaderboard(self, session_id: int) -> str:
        """Generate a leaderboard of most suspicious players."""
        if session_id not in self.suspicion_scores:
            return "❌ No suspicion data available for this session."
        
        scores = self.suspicion_scores[session_id]
        if not scores:
            return "❌ No suspicion data available."
        
        # Sort by suspicion score (highest first)
        sorted_players = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        # Get player names
        db = SessionLocal()
        try:
            leaderboard = []
            for player_id, score in sorted_players[:5]:  # Top 5
                player = db.query(Player).filter(Player.id == player_id).first()
                if player:
                    leaderboard.append({
                        "name": player.name,
                        "score": score
                    })
        finally:
            db.close()
        
        if not leaderboard:
            return "❌ No player data available."
        
        # Generate AI commentary
        top_suspicious = leaderboard[0]["name"] if leaderboard else "Unknown"
        commentary_prompt = f"""
The most suspicious player in this space station impostor game is {top_suspicious}.

Provide 1-2 sentences of detective commentary about the current suspicion levels.
Be observant and slightly mysterious.
"""
        
        commentary = await ai_client.generate_text("reasoning", commentary_prompt, 100)
        
        # Build leaderboard display
        display = "🕵️ **Suspicion Leaderboard**\n\n"
        for i, player in enumerate(leaderboard, 1):
            emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            display += f"{emoji} **{player['name']}** - {player['score']}/100\n"
        
        display += f"\n🤔 **AI Detective Commentary**\n{commentary}"
        
        return display
    
    def track_player_behavior(self, session_id: int, player_id: int, action_type: str, 
                            action_data: Dict):
        """Track individual player behaviors for analysis."""
        if session_id not in self.behavior_tracking:
            self.behavior_tracking[session_id] = {}
        
        if player_id not in self.behavior_tracking[session_id]:
            self.behavior_tracking[session_id][player_id] = {
                "vote_times": [],
                "vote_targets": [],
                "accusations": 0,
                "defensive_actions": 0,
                "messages_sent": 0,
                "suspicious_actions": 0
            }
        
        behavior = self.behavior_tracking[session_id][player_id]
        
        if action_type == "vote":
            behavior["vote_times"].append(action_data.get("time_taken", 0))
            behavior["vote_targets"].append(action_data.get("target", None))
        elif action_type == "accusation":
            behavior["accusations"] += 1
        elif action_type == "defensive":
            behavior["defensive_actions"] += 1
        elif action_type == "message":
            behavior["messages_sent"] += 1
        elif action_type == "suspicious":
            behavior["suspicious_actions"] += 1
    
    def get_suspicion_score(self, session_id: int, player_id: int) -> int:
        """Get current suspicion score for a player."""
        return self.suspicion_scores.get(session_id, {}).get(player_id, 0)
    
    def _collect_voting_data(self, session_id: int, round_number: int) -> Dict:
        """Collect voting data from database for analysis."""
        db = SessionLocal()
        try:
            votes = db.query(VoteHistory).filter(
                VoteHistory.session_id == session_id,
                VoteHistory.round_number == round_number
            ).all()
            
            voting_data = {
                "total_votes": len(votes),
                "vote_targets": {},
                "vote_times": [],
                "anonymous_votes": 0,
                "double_votes": 0
            }
            
            for vote in votes:
                # Count vote targets
                target = vote.target_id
                if target in voting_data["vote_targets"]:
                    voting_data["vote_targets"][target] += 1
                else:
                    voting_data["vote_targets"][target] = 1
                
                # Track special vote types
                if vote.anonymous_vote:
                    voting_data["anonymous_votes"] += 1
                if vote.double_vote:
                    voting_data["double_votes"] += 1
            
            return voting_data
        finally:
            db.close()
    
    def _analyze_voting_patterns(self, voting_data: Dict, vote_results: Dict) -> Dict:
        """Analyze voting patterns for suspicious behavior."""
        patterns = {
            "quick_voting": False,
            "group_voting": False,
            "suspicious_targets": [],
            "vote_manipulation": False,
            "unusual_behavior": []
        }
        
        # Check for quick voting (votes within 10 seconds)
        if voting_data.get("total_votes", 0) > 0:
            patterns["quick_voting"] = True
        
        # Check for group voting (3+ votes for same target)
        for target, count in voting_data["vote_targets"].items():
            if count >= 3:
                patterns["group_voting"] = True
                patterns["suspicious_targets"].append(target)
        
        # Check for vote manipulation
        if voting_data["anonymous_votes"] > 0 or voting_data["double_votes"] > 0:
            patterns["vote_manipulation"] = True
        
        return patterns
    
    async def _generate_ai_insights(self, session_id: int, patterns: Dict, 
                                  vote_results: Dict) -> str:
        """Generate AI-powered insights about voting behavior."""
        # Build context for AI
        context_parts = []
        
        if patterns["quick_voting"]:
            context_parts.append("Multiple players voted very quickly")
        
        if patterns["group_voting"]:
            context_parts.append("Group voting patterns detected")
        
        if patterns["vote_manipulation"]:
            context_parts.append("Vote manipulation abilities were used")
        
        if patterns["suspicious_targets"]:
            context_parts.append(f"High suspicion on targets: {patterns['suspicious_targets']}")
        
        context = "; ".join(context_parts) if context_parts else "Standard voting round"
        
        # Generate AI analysis
        vote_text = ", ".join([f"{k}: {v}" for k, v in vote_results.items()])
        
        analysis = await ai_client.generate_voting_analysis(
            vote_results, [context], f"Round analysis: {context}"
        )
        
        return analysis
    
    def _update_suspicion_scores(self, session_id: int, patterns: Dict):
        """Update suspicion scores based on voting patterns."""
        if session_id not in self.suspicion_scores:
            self.suspicion_scores[session_id] = {}
        
        # Get all players in session
        db = SessionLocal()
        try:
            links = db.query(PlayerGameLink).filter(
                PlayerGameLink.session_id == session_id,
                PlayerGameLink.left_at.is_(None)
            ).all()
            
            for link in links:
                player_id = link.player_id
                current_score = self.suspicion_scores[session_id].get(player_id, 0)
                
                # Adjust score based on patterns
                if patterns["quick_voting"]:
                    current_score += 5
                
                if player_id in patterns["suspicious_targets"]:
                    current_score += 10
                
                if patterns["vote_manipulation"]:
                    current_score += 15
                
                # Cap score at 100
                current_score = min(current_score, 100)
                
                self.suspicion_scores[session_id][player_id] = current_score
        finally:
            db.close()
    
    def _store_analysis(self, session_id: int, round_number: int, insights: str, 
                       patterns: Dict):
        """Store analysis results for future reference."""
        if session_id not in self.analysis_history:
            self.analysis_history[session_id] = []
        
        analysis_record = {
            "round": round_number,
            "insights": insights,
            "patterns": patterns,
            "timestamp": datetime.now()
        }
        
        self.analysis_history[session_id].append(analysis_record)
    
    def get_analysis_history(self, session_id: int) -> List[Dict]:
        """Get analysis history for a session."""
        return self.analysis_history.get(session_id, [])
    
    def cleanup_session_analysis(self, session_id: int):
        """Clean up analysis data for a finished session."""
        if session_id in self.voting_patterns:
            del self.voting_patterns[session_id]
        
        if session_id in self.analysis_history:
            del self.analysis_history[session_id]
        
        if session_id in self.suspicion_scores:
            del self.suspicion_scores[session_id]
        
        if session_id in self.behavior_tracking:
            del self.behavior_tracking[session_id]
        
        logger.info(f"Cleaned up voting analysis data for session {session_id}")


# Global instance
ai_voting_analyzer = AIVotingAnalyzer() 