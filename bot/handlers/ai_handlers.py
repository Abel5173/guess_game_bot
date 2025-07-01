"""
AI Handlers - Handle AI-powered features and commands.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from bot.ai import ai_game_engine
from bot.database import SessionLocal
from bot.database.models import Player, GameSession
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# AI FEATURE COMMANDS
# ============================================================================

async def ai_status_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show AI system status and enabled features."""
    user = update.effective_user
    
    enabled_features = ai_game_engine.get_enabled_features()
    
    status_text = "🤖 **AI System Status**\n\n"
    
    if enabled_features:
        status_text += "✅ **Enabled Features:**\n"
        for feature in enabled_features:
            feature_name = feature.replace("_", " ").title()
            status_text += f"• {feature_name}\n"
    else:
        status_text += "❌ **No AI features enabled**\n"
    
    status_text += "\n🔧 **AI Models:**\n"
    status_text += "• Narrative Generation: ✅\n"
    status_text += "• Task Creation: ✅\n"
    status_text += "• Voting Analysis: ✅\n"
    status_text += "• Chaos Events: ✅\n"
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎭 AI Personas", callback_data="ai_personas")],
        [InlineKeyboardButton("🕵️ AI Detective", callback_data="ai_detective")],
        [InlineKeyboardButton("⚡ Chaos Events", callback_data="ai_chaos")],
        [InlineKeyboardButton("📚 World Lore", callback_data="ai_lore")]
    ])
    
    await update.message.reply_text(
        status_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=keyboard
    )


async def ai_personas_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show AI-generated personas for current game."""
    user = update.effective_user
    
    # Get current game session for user
    db = SessionLocal()
    try:
        link = db.query(PlayerGameLink).filter(
            PlayerGameLink.player_id == user.id,
            PlayerGameLink.left_at.is_(None)
        ).first()
        
        if not link:
            await update.message.reply_text(
                "❌ **No active game found**\n\nJoin a game to see AI personas!",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        session_id = link.session_id
        personas = ai_game_engine.game_master.player_personas.get(session_id, {})
        
        if not personas:
            await update.message.reply_text(
                "❌ **No AI personas assigned**\n\nPersonas are assigned when games start.",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        display = "🎭 **AI-Generated Personas**\n\n"
        
        for player_id, persona_data in personas.items():
            player = db.query(Player).filter(Player.id == player_id).first()
            if player:
                display += f"**{player.name}**\n"
                display += f"🎭 {persona_data['description']}\n\n"
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Refresh Personas", callback_data="ai_refresh_personas")],
            [InlineKeyboardButton("📊 Persona Stats", callback_data="ai_persona_stats")]
        ])
        
        await update.message.reply_text(
            display,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard
        )
        
    finally:
        db.close()


async def ai_detective_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show AI detective analysis and suspicion scores."""
    user = update.effective_user
    
    # Get current game session
    db = SessionLocal()
    try:
        link = db.query(PlayerGameLink).filter(
            PlayerGameLink.player_id == user.id,
            PlayerGameLink.left_at.is_(None)
        ).first()
        
        if not link:
            await update.message.reply_text(
                "❌ **No active game found**\n\nJoin a game to see AI detective analysis!",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        session_id = link.session_id
        
        # Generate suspicion leaderboard
        leaderboard = await ai_game_engine.generate_suspicion_leaderboard(session_id)
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔍 My Analysis", callback_data="ai_my_analysis")],
            [InlineKeyboardButton("📈 Behavior Stats", callback_data="ai_behavior_stats")],
            [InlineKeyboardButton("🕵️ Detective Mode", callback_data="ai_detective_mode")]
        ])
        
        await update.message.reply_text(
            leaderboard,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard
        )
        
    finally:
        db.close()


async def ai_chaos_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show AI chaos events and trigger new ones."""
    user = update.effective_user
    
    # Get current game session
    db = SessionLocal()
    try:
        link = db.query(PlayerGameLink).filter(
            PlayerGameLink.player_id == user.id,
            PlayerGameLink.left_at.is_(None)
        ).first()
        
        if not link:
            await update.message.reply_text(
                "❌ **No active game found**\n\nJoin a game to see chaos events!",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        session_id = link.session_id
        
        # Get active chaos events
        active_events = ai_game_engine.chaos_events.get_active_events(session_id)
        
        if active_events:
            display = "⚡ **Active Chaos Events**\n\n"
            for event in active_events:
                display += f"**{event.name}**\n"
                display += f"{event.description}\n"
                display += f"⏰ Duration: {event.duration}s\n\n"
        else:
            display = "⚡ **No Active Chaos Events**\n\n"
            display += "Chaos events occur randomly during gameplay to add excitement!"
        
        # Get chaos stats
        stats = ai_game_engine.chaos_events.get_chaos_stats(session_id)
        display += f"📊 **Chaos Stats:**\n"
        display += f"• Total Events: {stats['total_events']}\n"
        display += f"• Most Common: {stats['most_common_type'] or 'None'}\n"
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎲 Trigger Event", callback_data="ai_trigger_chaos")],
            [InlineKeyboardButton("📊 Event History", callback_data="ai_chaos_history")],
            [InlineKeyboardButton("⚙️ Chaos Settings", callback_data="ai_chaos_settings")]
        ])
        
        await update.message.reply_text(
            display,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard
        )
        
    finally:
        db.close()


async def ai_lore_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate and display AI worldbuilding lore."""
    user = update.effective_user
    
    # Generate world lore
    lore = await ai_game_engine.generate_world_lore()
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📚 Generate New Lore", callback_data="ai_new_lore")],
        [InlineKeyboardButton("🌌 Station History", callback_data="ai_station_history")],
        [InlineKeyboardButton("🔮 Future Events", callback_data="ai_future_events")]
    ])
    
    await update.message.reply_text(
        lore,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=keyboard
    )


async def ai_task_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate a new AI task for the user."""
    user = update.effective_user
    
    # Get current game session
    db = SessionLocal()
    try:
        link = db.query(PlayerGameLink).filter(
            PlayerGameLink.player_id == user.id,
            PlayerGameLink.left_at.is_(None)
        ).first()
        
        if not link:
            await update.message.reply_text(
                "❌ **No active game found**\n\nJoin a game to get AI tasks!",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        session_id = link.session_id
        role = link.role
        
        # Generate AI task
        task = await ai_game_engine.generate_ai_task(session_id, user.id, role)
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Complete Task", callback_data="ai_complete_task")],
            [InlineKeyboardButton("🔄 New Task", callback_data="ai_new_task")],
            [InlineKeyboardButton("📋 Task History", callback_data="ai_task_history")]
        ])
        
        await update.message.reply_text(
            f"🤖 **AI-Generated Task**\n\n{task}",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard
        )
        
    finally:
        db.close()


# ============================================================================
# AI CALLBACK HANDLERS
# ============================================================================

async def handle_ai_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all AI-related callback queries."""
    query = update.callback_query
    data = query.data
    
    try:
        if data == "ai_personas":
            await ai_personas_handler(update, context)
        elif data == "ai_detective":
            await ai_detective_handler(update, context)
        elif data == "ai_chaos":
            await ai_chaos_handler(update, context)
        elif data == "ai_lore":
            await ai_lore_handler(update, context)
        elif data == "ai_my_analysis":
            await show_my_analysis(update, context)
        elif data == "ai_trigger_chaos":
            await trigger_chaos_event(update, context)
        elif data == "ai_new_lore":
            await generate_new_lore(update, context)
        elif data == "ai_new_task":
            await ai_task_handler(update, context)
        elif data == "ai_complete_task":
            await complete_ai_task(update, context)
        else:
            await query.answer("AI feature coming soon!")
            
    except Exception as e:
        logger.error(f"Error handling AI callback: {e}")
        await query.answer("❌ An error occurred!")


async def show_my_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show AI analysis for the current user."""
    query = update.callback_query
    user = update.effective_user
    
    # Get current game session
    db = SessionLocal()
    try:
        link = db.query(PlayerGameLink).filter(
            PlayerGameLink.player_id == user.id,
            PlayerGameLink.left_at.is_(None)
        ).first()
        
        if not link:
            await query.answer("No active game found!")
            return
        
        session_id = link.session_id
        
        # Generate behavior analysis
        analysis = await ai_game_engine.voting_analyzer.generate_player_behavior_report(
            session_id, user.id
        )
        
        await query.message.reply_text(
            analysis,
            parse_mode=ParseMode.MARKDOWN
        )
        
    finally:
        db.close()


async def trigger_chaos_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manually trigger a chaos event."""
    query = update.callback_query
    user = update.effective_user
    
    # Get current game session
    db = SessionLocal()
    try:
        link = db.query(PlayerGameLink).filter(
            PlayerGameLink.player_id == user.id,
            PlayerGameLink.left_at.is_(None)
        ).first()
        
        if not link:
            await query.answer("No active game found!")
            return
        
        session_id = link.session_id
        
        # Generate chaos event
        event = await ai_game_engine.chaos_events.generate_chaos_event(session_id)
        
        if event:
            event.activate()
            
            # Add to active events
            if session_id not in ai_game_engine.chaos_events.active_events:
                ai_game_engine.chaos_events.active_events[session_id] = []
            ai_game_engine.chaos_events.active_events[session_id].append(event)
            
            await query.message.reply_text(
                f"⚡ **Chaos Event Triggered!**\n\n{event.description}",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await query.answer("Failed to generate chaos event!")
        
    finally:
        db.close()


async def generate_new_lore(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate new world lore."""
    query = update.callback_query
    
    # Generate new lore
    lore = await ai_game_engine.generate_world_lore()
    
    await query.message.reply_text(
        lore,
        parse_mode=ParseMode.MARKDOWN
    )


async def complete_ai_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Complete the current AI task."""
    query = update.callback_query
    user = update.effective_user
    
    # Get current game session
    db = SessionLocal()
    try:
        link = db.query(PlayerGameLink).filter(
            PlayerGameLink.player_id == user.id,
            PlayerGameLink.left_at.is_(None)
        ).first()
        
        if not link:
            await query.answer("No active game found!")
            return
        
        session_id = link.session_id
        
        # Get active tasks
        active_tasks = ai_game_engine.task_generator.get_active_tasks(session_id, user.id)
        
        if not active_tasks:
            await query.answer("No active tasks to complete!")
            return
        
        # Complete the first active task
        task = active_tasks[0]
        success, xp_gained = ai_game_engine.task_generator.complete_task(
            session_id, user.id, task["id"]
        )
        
        if success:
            await query.message.reply_text(
                f"✅ **Task Completed!**\n\n"
                f"🎯 {task['description']}\n"
                f"✨ **XP Gained:** +{xp_gained}",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await query.answer("Failed to complete task!")
        
    finally:
        db.close() 