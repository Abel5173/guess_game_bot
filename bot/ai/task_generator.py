"""
AI Task Generator - Dynamic task creation using LLMs.
"""

import random
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging
from bot.ai.llm_client import ai_client
from bot.database import SessionLocal
from bot.database.models import Player, TaskLog

logger = logging.getLogger(__name__)


class AITaskGenerator:
    """AI-powered task generation system."""

    def __init__(self):
        logger.debug("Initializing AITaskGenerator")
        self.task_history = {}  # session_id -> [task_data]
        self.player_task_progress = {}  # session_id -> {player_id -> progress}
        self.task_templates = {
            "crewmate": {
                "easy": [
                    "Check oxygen levels in {location}",
                    "Calibrate {system} sensors",
                    "Restock {supply} in {location}",
                    "Run diagnostic on {equipment}",
                    "Monitor {system} readings",
                ],
                "medium": [
                    "Repair {system} malfunction in {location}",
                    "Analyze {data} from {source}",
                    "Coordinate {operation} between {location1} and {location2}",
                    "Investigate {anomaly} in {location}",
                    "Optimize {system} performance",
                ],
                "hard": [
                    "Override {system} safety protocols in {location}",
                    "Decrypt {data} from {source}",
                    "Reconfigure {network} topology",
                    "Emergency repair of {critical_system}",
                    "Coordinate multi-system {operation}",
                ],
            },
            "impostor": {
                "easy": [
                    "Create minor {system} disruption",
                    "Spread confusion about {topic}",
                    "Delay {operation} progress",
                    "Plant false {evidence}",
                    "Sabotage {equipment} subtly",
                ],
                "medium": [
                    "Frame {player} for {action}",
                    "Create major {system} malfunction",
                    "Spread paranoia about {suspicion}",
                    "Disrupt {communication} systems",
                    "Plant elaborate {deception}",
                ],
                "hard": [
                    "Execute complex {sabotage} plan",
                    "Manipulate {evidence} to frame {player}",
                    "Create cascading {system} failures",
                    "Orchestrate {deception} involving multiple players",
                    "Execute {master_plan} without detection",
                ],
            },
        }

        # Task locations and systems for template filling
        self.locations = [
            "Engineering Bay",
            "Medical Wing",
            "Navigation Deck",
            "Cargo Hold",
            "Communications Hub",
            "Life Support",
            "Power Grid",
            "Shield Generator",
            "Weapons Bay",
            "Science Lab",
            "Crew Quarters",
            "Command Bridge",
        ]

        self.systems = [
            "life support",
            "navigation",
            "communications",
            "power distribution",
            "shields",
            "weapons",
            "sensors",
            "thrusters",
            "artificial gravity",
            "environmental controls",
            "security",
            "medical systems",
        ]

        self.equipment = [
            "oxygen scrubbers",
            "fusion reactors",
            "plasma conduits",
            "quantum computers",
            "holographic projectors",
            "tractor beams",
            "warp drives",
            "phaser arrays",
            "transporter pads",
            "replicators",
            "holodecks",
            "deflector dishes",
        ]

        self.supplies = [
            "medical supplies",
            "food rations",
            "spare parts",
            "energy cells",
            "oxygen tanks",
            "water containers",
            "repair kits",
            "emergency gear",
        ]

    async def generate_task(
        self, session_id: int, player_id: int, role: str, difficulty: str = None
    ) -> Dict:
        """Generate a unique AI task for a player."""
        logger.info(
            f"generate_task called with session_id={session_id}, player_id={player_id}, role={role}, difficulty={difficulty}"
        )
        # Get player info
        db = SessionLocal()
        try:
            player = db.query(Player).filter(Player.id == player_id).first()
            player_name = player.name if player else "Crew Member"
        finally:
            db.close()

        # Determine difficulty if not specified
        if not difficulty:
            difficulty = self._determine_difficulty(session_id, player_id)

        # Generate task using AI
        task_description = await ai_client.generate_dynamic_task(
            role, player_name, difficulty, "Space Station"
        )

        # Create task data
        task_data = {
            "id": f"task_{session_id}_{player_id}_{int(datetime.now().timestamp())}",
            "player_id": player_id,
            "role": role,
            "difficulty": difficulty,
            "description": task_description,
            "created_at": datetime.now(),
            "completed": False,
            "xp_reward": self._calculate_xp_reward(difficulty, role),
            "ai_generated": True,
        }

        # Store task history
        if session_id not in self.task_history:
            self.task_history[session_id] = []
        self.task_history[session_id].append(task_data)

        # Initialize progress tracking
        if session_id not in self.player_task_progress:
            self.player_task_progress[session_id] = {}
        if player_id not in self.player_task_progress[session_id]:
            self.player_task_progress[session_id][player_id] = {
                "tasks_assigned": 0,
                "tasks_completed": 0,
                "total_xp_earned": 0,
            }

        self.player_task_progress[session_id][player_id]["tasks_assigned"] += 1

        logger.info(f"Generated task for player {player_id} in session {session_id}")

        return task_data

    async def generate_batch_tasks(
        self, session_id: int, player_ids: List[int], roles: Dict[int, str]
    ) -> Dict[int, Dict]:
        """Generate tasks for multiple players at once."""
        tasks = {}

        for player_id in player_ids:
            role = roles.get(player_id, "crewmate")
            task = await self.generate_task(session_id, player_id, role)
            tasks[player_id] = task

        return tasks

    def complete_task(
        self, session_id: int, player_id: int, task_id: str
    ) -> Tuple[bool, int]:
        """Mark a task as completed and award XP."""
        logger.debug(
            f"complete_task called with session_id={session_id}, player_id={player_id}, task_id={task_id}"
        )
        if session_id not in self.task_history:
            logger.warning(f"Session {session_id} not found in task history.")
            return False, 0

        # Find the task
        task = None
        for t in self.task_history[session_id]:
            if (
                t["id"] == task_id
                and t["player_id"] == player_id
                and not t["completed"]
            ):
                task = t
                break

        if not task:
            logger.warning(
                f"Task with ID {task_id} not found for player {player_id} in session {session_id} or already completed."
            )
            return False, 0

        # Mark as completed
        task["completed"] = True
        task["completed_at"] = datetime.now()

        # Award XP
        xp_reward = task["xp_reward"]

        # Update progress
        if (
            session_id in self.player_task_progress
            and player_id in self.player_task_progress[session_id]
        ):
            self.player_task_progress[session_id][player_id]["tasks_completed"] += 1
            self.player_task_progress[session_id][player_id][
                "total_xp_earned"
            ] += xp_reward

        # Log to database
        self._log_task_completion(session_id, player_id, task)

        logger.info(f"Task completed: {task_id} by player {player_id}, +{xp_reward} XP")

        return True, xp_reward

    def get_player_tasks(self, session_id: int, player_id: int) -> List[Dict]:
        """Get all tasks for a player in a session."""
        logger.debug(
            f"get_player_tasks called with session_id={session_id}, player_id={player_id}"
        )
        if session_id not in self.task_history:
            logger.warning(f"Session {session_id} not found in task history.")
            return []

        return [
            task
            for task in self.task_history[session_id]
            if task["player_id"] == player_id
        ]

    def get_active_tasks(self, session_id: int, player_id: int) -> List[Dict]:
        """Get active (incomplete) tasks for a player."""
        logger.debug(
            f"get_active_tasks called with session_id={session_id}, player_id={player_id}"
        )
        tasks = self.get_player_tasks(session_id, player_id)
        return [task for task in tasks if not task["completed"]]

    def get_task_progress(self, session_id: int, player_id: int) -> Dict:
        """Get task progress statistics for a player."""
        logger.debug(
            f"get_task_progress called with session_id={session_id}, player_id={player_id}"
        )
        if (
            session_id not in self.player_task_progress
            or player_id not in self.player_task_progress[session_id]
        ):
            logger.warning(
                f"Player {player_id} in session {session_id} not found in player task progress."
            )
            return {
                "tasks_assigned": 0,
                "tasks_completed": 0,
                "total_xp_earned": 0,
                "completion_rate": 0.0,
            }

        progress = self.player_task_progress[session_id][player_id]
        assigned = progress["tasks_assigned"]
        completed = progress["tasks_completed"]

        return {
            **progress,
            "completion_rate": (completed / assigned * 100) if assigned > 0 else 0.0,
        }

    def generate_task_summary(self, session_id: int, player_id: int) -> str:
        """Generate a summary of player's task performance."""
        logger.debug(
            f"generate_task_summary called with session_id={session_id}, player_id={player_id}"
        )
        progress = self.get_task_progress(session_id, player_id)
        active_tasks = self.get_active_tasks(session_id, player_id)

        summary = f"📋 **Task Summary**\n\n"
        summary += f"✅ **Completed:** {progress['tasks_completed']}\n"
        summary += f"📊 **Success Rate:** {progress['completion_rate']:.1f}%\n"
        summary += f"✨ **XP Earned:** {progress['total_xp_earned']}\n"

        if active_tasks:
            summary += f"\n🔄 **Active Tasks:** {len(active_tasks)}\n"
            for task in active_tasks[:3]:  # Show top 3
                summary += f"• {task['description']}\n"

        return summary

    def _determine_difficulty(self, session_id: int, player_id: int) -> str:
        """Determine task difficulty based on player performance and game state."""
        logger.debug(
            f"_determine_difficulty called with session_id={session_id}, player_id={player_id}"
        )
        progress = self.get_task_progress(session_id, player_id)

        # Base difficulty on completion rate
        completion_rate = progress["completion_rate"]

        if completion_rate >= 80:
            return "hard"
        elif completion_rate >= 60:
            return "medium"
        else:
            return "easy"

    def _calculate_xp_reward(self, difficulty: str, role: str) -> int:
        """Calculate XP reward for task completion."""
        logger.debug(
            f"_calculate_xp_reward called with difficulty={difficulty}, role={role}"
        )
        base_rewards = {"easy": 10, "medium": 25, "hard": 50}

        base_xp = base_rewards.get(difficulty, 10)

        # Bonus for impostor tasks (they're harder to complete)
        if role == "impostor":
            base_xp = int(base_xp * 1.5)

        return base_xp

    def _log_task_completion(self, session_id: int, player_id: int, task: Dict):
        """Log task completion to database."""
        logger.debug(
            f"_log_task_completion called with session_id={session_id}, player_id={player_id}"
        )
        db = SessionLocal()
        try:
            task_log = TaskLog(
                session_id=session_id,
                player_id=player_id,
                task_type="ai_generated",
                task_description=task["description"],
                xp_earned=task["xp_reward"],
                completed_at=datetime.now(),
            )
            db.add(task_log)
            db.commit()
        except Exception as e:
            logger.error(f"Failed to log task completion: {e}")
            db.rollback()
        finally:
            db.close()

    def cleanup_session_tasks(self, session_id: int):
        """Clean up task data for a finished session."""
        logger.debug(f"cleanup_session_tasks called with session_id={session_id}")
        if session_id in self.task_history:
            del self.task_history[session_id]

        if session_id in self.player_task_progress:
            del self.player_task_progress[session_id]

        logger.info(f"Cleaned up task data for session {session_id}")


# Global instance
ai_task_generator = AITaskGenerator()
