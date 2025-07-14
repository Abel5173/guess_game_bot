"""
AI Chaos Events - Random dramatic events to add excitement and unpredictability.
"""

import random
import asyncio
from typing import Dict, List, Optional, Tuple, Callable
from datetime import datetime, timedelta
import logging
from bot.ai.llm_client import ai_client
from bot.database import SessionLocal
from bot.database.models import GameSession, PlayerGameLink

logger = logging.getLogger(__name__)


class ChaosEvent:
    """Represents a chaos event that can occur during gameplay."""
    
    def __init__(self, event_id: str, name: str, description: str, 
                 event_type: str, duration: int, effects: Dict):
        self.event_id = event_id
        self.name = name
        self.description = description
        self.event_type = event_type  # system_failure, ai_intervention, mystery, environmental
        self.duration = duration  # seconds
        self.effects = effects
        self.triggered_at = None
        self.active = False
    
    def activate(self):
        """Activate the chaos event."""
        self.triggered_at = datetime.now()
        self.active = True
    
    def is_expired(self) -> bool:
        """Check if the event has expired."""
        if not self.triggered_at:
            return False
        return datetime.now() - self.triggered_at > timedelta(seconds=self.duration)


class AIChaosEvents:
    """AI-powered chaos events system."""
    
    def __init__(self):
        self.active_events = {}  # session_id -> [ChaosEvent]
        self.event_history = {}  # session_id -> [event_data]
        self.event_timers = {}  # session_id -> next_event_time
        self.event_callbacks = {}  # event_type -> callback_function
        
        # Event templates
        self.event_templates = {
            "system_failure": {
                "probability": 0.3,
                "min_interval": 180,  # 3 minutes
                "max_interval": 600,  # 10 minutes
                "duration_range": (60, 180)  # 1-3 minutes
            },
            "ai_intervention": {
                "probability": 0.2,
                "min_interval": 300,  # 5 minutes
                "max_interval": 900,  # 15 minutes
                "duration_range": (120, 300)  # 2-5 minutes
            },
            "mystery_event": {
                "probability": 0.15,
                "min_interval": 240,  # 4 minutes
                "max_interval": 720,  # 12 minutes
                "duration_range": (90, 240)  # 1.5-4 minutes
            },
            "environmental": {
                "probability": 0.25,
                "min_interval": 200,  # 3.3 minutes
                "max_interval": 600,  # 10 minutes
                "duration_range": (60, 150)  # 1-2.5 minutes
            }
        }
        
        # Register default event callbacks
        self._register_default_callbacks()
    
    async def check_for_chaos_events(self, session_id: int) -> List[ChaosEvent]:
        """Check if any chaos events should be triggered."""
        triggered_events = []
        
        # Check if it's time for an event
        if not self._should_trigger_event(session_id):
            return triggered_events
        
        # Determine event type based on probabilities
        event_type = self._select_event_type()
        
        # Generate and trigger event
        event = await self._generate_chaos_event(session_id, event_type)
        if event:
            event.activate()
            triggered_events.append(event)
            
            # Store in active events
            if session_id not in self.active_events:
                self.active_events[session_id] = []
            self.active_events[session_id].append(event)
            
            # Update timer
            self._update_event_timer(session_id, event_type)
            
            # Log event
            self._log_event(session_id, event)
            
            # Execute callback if registered
            if event_type in self.event_callbacks:
                await self.event_callbacks[event_type](session_id, event)
        
        return triggered_events
    
    async def generate_chaos_event(self, session_id: int, event_type: str = None) -> Optional[ChaosEvent]:
        """Generate a specific chaos event."""
        if not event_type:
            event_type = self._select_event_type()
        
        return await self._generate_chaos_event(session_id, event_type)
    
    def get_active_events(self, session_id: int) -> List[ChaosEvent]:
        """Get currently active chaos events for a session."""
        events = self.active_events.get(session_id, [])
        # Filter out expired events
        active_events = [event for event in events if not event.is_expired()]
        
        # Update active events list
        self.active_events[session_id] = active_events
        
        return active_events
    
    def register_event_callback(self, event_type: str, callback: Callable):
        """Register a callback function for a specific event type."""
        self.event_callbacks[event_type] = callback
    
    def get_event_history(self, session_id: int) -> List[Dict]:
        """Get chaos event history for a session."""
        return self.event_history.get(session_id, [])
    
    def get_chaos_stats(self, session_id: int) -> Dict:
        """Get chaos event statistics for a session."""
        history = self.get_event_history(session_id)
        
        stats = {
            "total_events": len(history),
            "events_by_type": {},
            "total_duration": 0,
            "most_common_type": None
        }
        
        for event_data in history:
            event_type = event_data["event_type"]
            if event_type not in stats["events_by_type"]:
                stats["events_by_type"][event_type] = 0
            stats["events_by_type"][event_type] += 1
            
            stats["total_duration"] += event_data.get("duration", 0)
        
        if stats["events_by_type"]:
            stats["most_common_type"] = max(stats["events_by_type"].items(), 
                                          key=lambda x: x[1])[0]
        
        return stats
    
    async def _generate_chaos_event(self, session_id: int, event_type: str) -> Optional[ChaosEvent]:
        """Generate a chaos event of the specified type."""
        # Get game context
        game_context = self._get_game_context(session_id)

        # Generate event description using AI
        event_data = await ai_client.generate_chaos_event(
            game_state=game_context["state"],
            player_count=game_context["alive_count"]
        )
        description = event_data.get("description", "A mysterious event unfolds.")
        
        # Determine duration
        template = self.event_templates.get(event_type, {})
        duration_range = template.get("duration_range", (60, 180))
        duration = random.randint(*duration_range)
        
        # Create event effects
        effects = self._generate_event_effects(event_type, duration)
        
        # Create event
        event_id = f"chaos_{session_id}_{event_type}_{int(datetime.now().timestamp())}"
        event_name = self._get_event_name(event_type)
        
        chaos_event = ChaosEvent(
            event_id=event_id,
            name=event_name,
            description=description,
            event_type=event_type,
            duration=duration,
            effects=effects
        )
        
        logger.info(f"Generated chaos event: {event_name} for session {session_id}")
        
        return chaos_event
    
    def _should_trigger_event(self, session_id: int) -> bool:
        """Check if a chaos event should be triggered."""
        if session_id not in self.event_timers:
            self.event_timers[session_id] = datetime.now()
            return False
        
        last_event = self.event_timers[session_id]
        time_since_event = datetime.now() - last_event
        
        # Minimum interval between events
        min_interval = 120  # 2 minutes
        return time_since_event.total_seconds() > min_interval
    
    def _select_event_type(self) -> str:
        """Select an event type based on probabilities."""
        event_types = list(self.event_templates.keys())
        probabilities = [self.event_templates[et]["probability"] for et in event_types]
        
        # Normalize probabilities
        total_prob = sum(probabilities)
        if total_prob == 0:
            return random.choice(event_types)
        
        normalized_probs = [p / total_prob for p in probabilities]
        
        # Select based on probability
        rand = random.random()
        cumulative = 0
        
        for i, prob in enumerate(normalized_probs):
            cumulative += prob
            if rand <= cumulative:
                return event_types[i]
        
        return event_types[-1]  # Fallback
    
    def _update_event_timer(self, session_id: int, event_type: str):
        """Update the event timer for a session."""
        template = self.event_templates.get(event_type, {})
        min_interval = template.get("min_interval", 180)
        max_interval = template.get("max_interval", 600)
        
        # Random interval between min and max
        interval = random.randint(min_interval, max_interval)
        next_event = datetime.now() + timedelta(seconds=interval)
        
        self.event_timers[session_id] = next_event
    
    def _generate_event_effects(self, event_type: str, duration: int) -> Dict:
        """Generate effects for a chaos event."""
        effects = {
            "duration": duration,
            "affects_voting": False,
            "affects_tasks": False,
            "affects_communication": False,
            "special_rules": []
        }
        
        if event_type == "system_failure":
            effects["affects_tasks"] = True
            effects["special_rules"].append("Task completion takes 50% longer")
        
        elif event_type == "ai_intervention":
            effects["affects_voting"] = True
            effects["special_rules"].append("AI casts a mystery vote")
        
        elif event_type == "mystery_event":
            effects["affects_communication"] = True
            effects["special_rules"].append("Some messages are scrambled")
        
        elif event_type == "environmental":
            effects["affects_tasks"] = True
            effects["affects_voting"] = True
            effects["special_rules"].append("All actions have random delays")
        
        return effects
    
    def _get_event_name(self, event_type: str) -> str:
        """Get a display name for an event type."""
        names = {
            "system_failure": "🚨 System Failure",
            "ai_intervention": "🤖 AI Intervention", 
            "mystery_event": "❓ Mystery Event",
            "environmental": "🌪️ Environmental Hazard"
        }
        return names.get(event_type, "⚡ Chaos Event")
    
    def _get_game_context(self, session_id: int) -> Dict:
        """Get current game context for event generation."""
        db = SessionLocal()
        try:
            # Get alive player count
            alive_count = db.query(PlayerGameLink).filter(
                PlayerGameLink.session_id == session_id,
                PlayerGameLink.left_at.is_(None)
            ).count()
            
            # Get game session info
            session = db.query(GameSession).filter(GameSession.id == session_id).first()
            rounds = 0
            if session and session.game_state:
                rounds = session.game_state.get("rounds", 0)
            
            return {
                "state": f"Active game with {alive_count} players",
                "alive_count": alive_count,
                "rounds": rounds
            }
        finally:
            db.close()
    
    def _log_event(self, session_id: int, event: ChaosEvent):
        """Log a chaos event to history."""
        if session_id not in self.event_history:
            self.event_history[session_id] = []
        
        event_data = {
            "event_id": event.event_id,
            "name": event.name,
            "description": event.description,
            "event_type": event.event_type,
            "duration": event.duration,
            "triggered_at": event.triggered_at,
            "effects": event.effects
        }
        
        self.event_history[session_id].append(event_data)
    
    def _register_default_callbacks(self):
        """Register default callback functions for events."""
        # System failure callback
        self.register_event_callback("system_failure", self._system_failure_callback)
        
        # AI intervention callback
        self.register_event_callback("ai_intervention", self._ai_intervention_callback)
        
        # Mystery event callback
        self.register_event_callback("mystery_event", self._mystery_event_callback)
        
        # Environmental callback
        self.register_event_callback("environmental", self._environmental_callback)
    
    async def _system_failure_callback(self, session_id: int, event: ChaosEvent):
        """Callback for system failure events."""
        logger.info(f"System failure event triggered in session {session_id}")
        # Could implement task slowdown logic here
    
    async def _ai_intervention_callback(self, session_id: int, event: ChaosEvent):
        """Callback for AI intervention events."""
        logger.info(f"AI intervention event triggered in session {session_id}")
        # Could implement AI vote casting here
    
    async def _mystery_event_callback(self, session_id: int, event: ChaosEvent):
        """Callback for mystery events."""
        logger.info(f"Mystery event triggered in session {session_id}")
        # Could implement message scrambling here
    
    async def _environmental_callback(self, session_id: int, event: ChaosEvent):
        """Callback for environmental events."""
        logger.info(f"Environmental event triggered in session {session_id}")
        # Could implement random delays here
    
    def cleanup_session_events(self, session_id: int):
        """Clean up chaos event data for a finished session."""
        if session_id in self.active_events:
            del self.active_events[session_id]
        
        if session_id in self.event_history:
            del self.event_history[session_id]
        
        if session_id in self.event_timers:
            del self.event_timers[session_id]
        
        logger.info(f"Cleaned up chaos events data for session {session_id}")


# Global instance
ai_chaos_events = AIChaosEvents() 