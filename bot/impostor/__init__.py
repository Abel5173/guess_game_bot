from .core import ImpostorCore
from .phases import PhaseManager
from .voting import VotingManager
from .ai_clues import AIClueManager
from telegram.constants import ParseMode
from bot.tasks.clue_tasks import get_random_task
from bot.database import SessionLocal
from bot.database.models import Task, Player
from bot.database.session_manager import GameSessionManager
from sqlalchemy import func
from bot.ui.buttons import main_menu, voting_menu, confirm_end_game
from telegram import Update
from bot.impostor.utils import calculate_title


class ImpostorGame:
    """
    Orchestrator/facade for the modular Impostor Game. Exposes a clean interface for handlers.
    Now uses a database for persistent player stats and session tracking.
    """

    def __init__(self, config=None):
        self.core = ImpostorCore(config)
        self.ai_clues = AIClueManager(self.core)
        self.phases = PhaseManager(self.core, self.ai_clues)
        self.voting = VotingManager(self.core)
        self.core.votes = {}
        self.core.discussion_history = []
        self.current_tasks = {}  # user_id: expected answer
        self.session_manager = GameSessionManager()
        self.db_session_id = None  # Will be set when game is created in a topic

    def set_db_session_id(self, session_id: int):
        """Set the database session ID for this game."""
        self.db_session_id = session_id

    def add_player(self, user_id, name):
        return self.core.add_player(user_id, name)

    def get_type(self):
        return "impostor"

    def get_game(self):
        return self

    async def join_impostor(self, update, context):
        user = update.effective_user
        msg = update.message or (
            update.callback_query and update.callback_query.message
        )
        if self.add_player(user.id, user.first_name):
            if msg:
                await msg.reply_text(f"✅ {user.first_name} joined the game.")
        else:
            if msg:
                await msg.reply_text(
                    "⚠️ You are already in the game or the game has started."
                )

    async def start_impostor_game(self, update, context):
        self.core.group_chat_id = update.effective_chat.id
        msg = update.message or (
            update.callback_query and update.callback_query.message
        )
        if not self.core.start_game():
            if msg:
                await msg.reply_text("❗ Need at least 4 players to start.")
            return
        for uid, name in self.core.players.items():
            try:
                await context.bot.send_message(
                    uid, "🎭 You are a player in the game.", parse_mode="HTML"
                )
            except Exception:
                pass
        await self.phases.start_task_phase(context)

    async def handle_discussion(self, update, context):
        if self.core.phase != "discussion":
            return
        user = update.effective_user
        text = update.message.text.strip()
        if user.id in self.core.players:
            self.core.discussion_history.append(
                f"{self.core.players[user.id]['name']}: {text}"
            )
            
            # Log discussion in database if we have a session ID
            if self.db_session_id:
                try:
                    self.session_manager.log_discussion(
                        self.db_session_id, user.id, text, "discussion"
                    )
                except Exception as e:
                    print(f"Failed to log discussion: {e}")

    async def handle_vote(self, update, context):
        await self.voting.handle_vote(update, context)

    async def complete_task(self, update):
        user = update.effective_user
        is_impostor = user.id in self.core.impostors
        xp, title = self.core.award_task_xp(user.id, is_impostor)
        if xp is not None:
            return f"✅ {user.first_name} gained XP! New XP: {xp}, Title: {title}"
        return "⚠️ You're not in the DB. Use /startgame first."

    async def show_main_menu(self, update: Update):
        msg = update.message or (
            update.callback_query and update.callback_query.message
        )
        await msg.reply_text("🎮 Choose an action:", reply_markup=main_menu())

    async def handle_join_game(self, update, context):
        user = update.effective_user
        msg = update.callback_query.message if update.callback_query else update.message
        if self.add_player(user.id, user.first_name):
            await msg.reply_text(f"✅ {user.first_name} joined the game.")
        else:
            await msg.reply_text(
                "⚠️ You are already in the game or the game has started."
            )
        await self.show_main_menu(update)

    async def handle_complete_task(self, update, context):
        user = update.effective_user
        db = SessionLocal()
        player = db.query(Player).filter(Player.id == user.id).first()
        if player:
            xp_gain = 10 if user.id not in self.core.impostors else 5
            player.xp += xp_gain
            if user.id not in self.core.impostors:
                player.tasks_done += 1
            else:
                player.fake_tasks_done += 1
            player.title = calculate_title(player.xp)
            db.commit()
            
            # Log task completion in database if we have a session ID
            if self.db_session_id:
                try:
                    task_type = "crewmate_task" if user.id not in self.core.impostors else "impostor_fake_task"
                    self.session_manager.log_task_completion(
                        self.db_session_id, user.id, task_type, 
                        f"Task completed by {user.first_name}", xp_gain
                    )
                except Exception as e:
                    print(f"Failed to log task completion: {e}")
            
            msg = f"✅ {player.name} gained XP! New XP: {player.xp}, Title: {player.title}"
        else:
            msg = "⚠️ You're not in the DB. Use Join Game first."
        db.close()
        await update.callback_query.message.reply_text(msg)
        await self.show_main_menu(update)

    async def handle_start_voting(self, update, context):
        self.core.phase = "voting"
        alive_players = self.core.get_alive_players()
        await update.callback_query.message.reply_text(
            "🗳️ Voting Phase — Vote who to eject!",
            reply_markup=voting_menu(alive_players),
        )

    async def handle_start_discussion(self, update, context):
        self.core.phase = "discussion"
        await update.callback_query.message.reply_text(
            "🗣️ Discussion Phase started! Discuss who the impostor might be.",
            reply_markup=main_menu(),
        )

    async def handle_end_game(self, update, context):
        await update.callback_query.message.reply_text(
            "Are you sure you want to end the game?", reply_markup=confirm_end_game()
        )

    async def handle_confirm_end_game(self, update, context):
        await self.reset()
        await update.callback_query.message.reply_text(
            "Game ended. Thanks for playing! 🎉", reply_markup=main_menu()
        )

    async def handle_cancel_end_game(self, update, context):
        await update.callback_query.message.reply_text(
            "End game cancelled.", reply_markup=main_menu()
        )

    async def show_profile(self, update):
        user = update.effective_user
        db = SessionLocal()
        player = db.query(Player).filter(Player.id == user.id).first()
        if not player:
            await update.callback_query.message.reply_text(
                "❌ You have not joined the game yet."
            )
            db.close()
            return
        msg = (
            f"📄 <b>Profile</b> — {player.name}\n"
            f"🏷️ Title: <code>{player.title}</code>\n"
            f"✨ XP: <b>{player.xp}</b>\n"
            f"🔧 Tasks Done: {player.tasks_done}\n"
            f"🛠️ Faked Tasks: {player.fake_tasks_done}"
        )
        db.close()
        await update.callback_query.message.reply_text(msg, parse_mode=ParseMode.HTML)
        await self.show_main_menu(update)

    async def show_leaderboard(self, update):
        db = SessionLocal()
        top_players = db.query(Player).order_by(Player.xp.desc()).limit(10).all()
        lines = ["🏆 <b>Leaderboard</b> — Top Players"]
        for i, p in enumerate(top_players, start=1):
            lines.append(f"{i}. {p.name} — {p.xp} XP ({p.title})")
        db.close()
        await update.callback_query.message.reply_text(
            "\n".join(lines), parse_mode=ParseMode.HTML
        )
        await self.show_main_menu(update)

    async def celebrate_win(self, update, winning_team):
        if winning_team == "crewmates":
            msg = "🎉 <b>Crewmates win!</b>"
        else:
            msg = "💀 <b>Impostors win!</b>"
        await update.callback_query.message.reply_text(msg, parse_mode=ParseMode.HTML)
        await self.show_main_menu(update)

    async def reset(self, update=None):
        self.core.reset()
        if update:
            await update.callback_query.message.reply_text(
                "🔄 Game has been reset.", reply_markup=main_menu()
            )

    async def task_command(self, update, context):
        user = update.effective_user
        chat_id = update.effective_chat.id
        db = SessionLocal()
        # Only allow one pending task per user
        existing = (
            db.query(Task)
            .filter(
                Task.user_id == user.id,
                Task.chat_id == chat_id,
                Task.status == "pending",
            )
            .first()
        )
        if existing:
            await update.message.reply_text(
                "❗ You already have a pending task. Use /answer to answer it."
            )
            db.close()
            return
        player_names = list(self.core.players.values())
        discussion = (
            "\n".join(self.core.discussion_history)
            if self.core.discussion_history
            else None
        )
        task_type, puzzle, answer = await get_random_task(player_names, discussion)
        task = Task(
            user_id=user.id,
            chat_id=chat_id,
            task_type=task_type,
            puzzle=puzzle,
            answer=answer.lower(),
        )
        db.add(task)
        db.commit()
        db.close()
        await update.message.reply_text(
            f"🎯 Your task:\n\n{puzzle}\n\nReply with /answer <your answer>"
        )

    async def answer_command(self, update, context):
        user = update.effective_user
        chat_id = update.effective_chat.id
        db = SessionLocal()
        task = (
            db.query(Task)
            .filter(
                Task.user_id == user.id,
                Task.chat_id == chat_id,
                Task.status == "pending",
            )
            .first()
        )
        if not task:
            await update.message.reply_text(
                "❌ You don't have any active task. Use /task to get one."
            )
            db.close()
            return
        if not context.args:
            await update.message.reply_text(
                "❗ Please provide an answer after the command."
            )
            db.close()
            return
        user_answer = " ".join(context.args).lower()
        if user_answer == task.answer:
            task.status = "completed"
            db.commit()
            db.close()
            msg = await self.complete_task(update)
            await update.message.reply_text(f"✅ Correct! {msg}")
        else:
            task.status = "failed"
            db.commit()
            db.close()
            await update.message.reply_text(
                "❌ Incorrect answer. Try again or use /task for a new one."
            )

    async def taskstats_command(self, update, context):
        user = update.effective_user
        chat_id = update.effective_chat.id
        db = SessionLocal()
        total = (
            db.query(Task)
            .filter(Task.user_id == user.id, Task.chat_id == chat_id)
            .count()
        )
        completed = (
            db.query(Task)
            .filter(
                Task.user_id == user.id,
                Task.chat_id == chat_id,
                Task.status == "completed",
            )
            .count()
        )
        failed = (
            db.query(Task)
            .filter(
                Task.user_id == user.id,
                Task.chat_id == chat_id,
                Task.status == "failed",
            )
            .count()
        )
        by_type = (
            db.query(Task.task_type, Task.status, func.count())
            .filter(Task.user_id == user.id, Task.chat_id == chat_id)
            .group_by(Task.task_type, Task.status)
            .all()
        )
        db.close()
        lines = [
            f"📊 <b>Task Stats</b> for {user.first_name}",
            f"Total: {total}",
            f"✅ Completed: {completed}",
            f"❌ Failed: {failed}",
        ]
        for ttype, status, count in by_type:
            lines.append(f"{ttype} ({status}): {count}")
        await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)

    async def show_rules(self, update):
        rules = (
            "<b>Impostor Game Rules</b>\n\n"
            "Welcome to the Impostor Game! Play with friends in a social deduction challenge inspired by Among Us.\n\n"
            "<b>How to Play:</b>\n"
            "• <b>Join the Game:</b> Click 'Join Game' to enter the lobby. When enough players join, the game can start!\n"
            "• <b>Roles:</b> Most are <b>Crewmates</b>, but a few are secret <b>Impostors</b>!\n"
            "• <b>Tasks:</b> Crewmates complete fun tasks to earn XP and help their team. Impostors fake tasks and try to blend in.\n"
            "• <b>Discussion:</b> After tasks, discuss who seems suspicious.\n"
            "• <b>Voting:</b> Vote to eject a suspected impostor. But beware—if you vote out a crewmate, the impostors get closer to victory!\n"
            "• <b>Win:</b> Crewmates win by completing all tasks or ejecting all impostors. Impostors win if they equal or outnumber crewmates.\n\n"
            "<b>Tips:</b>\n"
            "- Use the buttons for all actions—no typing needed!\n"
            "- Check your profile and leaderboard for stats and titles.\n"
            "- Have fun, play fair, and enjoy the mystery!\n\n"
            "<i>Ready to play? Use the menu below to get started!</i>"
        )
        await update.callback_query.message.reply_text(rules, parse_mode=ParseMode.HTML)
        await self.show_main_menu(update)
