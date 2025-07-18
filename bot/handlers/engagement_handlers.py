"""
Engagement Handlers - Handle all engagement feature interactions.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from bot.engagement import engagement_engine
from bot.engagement.crate_system import CrateType
from bot.engagement.status_system import TitleRarity
from bot.engagement.basecamp_system import RoomTheme, TrophyType
from bot.engagement.risk_reward_system import WagerType
from bot.engagement.mission_system import MissionType
from bot.engagement.flash_games_system import FlashEventType
from bot.engagement.betrayal_cards_system import CardType
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# CRATE SYSTEM HANDLERS
# ============================================================================


async def open_crate_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle crate opening requests."""
    user = update.effective_user
    logger.info(f"open_crate_handler called by user {user.id}")

    # For now, we'll simulate a game result to test crate opening
    # In real implementation, this would be called after game completion
    game_result = {"won": True, "mvp": False, "tasks_completed": 3, "role": "crewmate"}

    crate_type = engagement_engine.crate_system.determine_crate_type(game_result)
    reward, message = engagement_engine.crate_system.open_crate(crate_type, user.id)

    await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)


# ============================================================================
# STATUS SYSTEM HANDLERS
# ============================================================================


async def show_titles_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show available titles for the player."""
    user = update.effective_user
    logger.info(f"show_titles_handler called by user {user.id}")
    available_titles = engagement_engine.status_system.get_available_titles(user.id)

    if not available_titles:
        await update.message.reply_text(
            "🏷️ **No titles available**\n\nPlay more games to unlock titles!"
        )
        return

    display = "🏷️ **Available Titles**\n\n"

    for title_name in available_titles:
        title_info = engagement_engine.status_system.get_title_info(title_name)
        if title_info:
            rarity_emoji = {
                "common": "⚪",
                "rare": "🔵",
                "epic": "🟣",
                "legendary": "🟡",
                "mythic": "🔴",
                "limited": "💎",
            }.get(title_info["rarity"], "⚪")

            display += (
                f"{rarity_emoji} **{title_name}**\n"
                f"   📝 {title_info['rarity'].title()}\n\n"
            )

    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🏷️ Change Title", callback_data="change_title")],
            [InlineKeyboardButton("📊 Title Info", callback_data="title_info")],
        ]
    )

    await update.message.reply_text(
        display, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard
    )


# ============================================================================
# BASECAMP SYSTEM HANDLERS
# ============================================================================


async def show_basecamp_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show player's basecamp."""
    user = update.effective_user
    logger.info(f"show_basecamp_handler called by user {user.id}")
    basecamp_display = engagement_engine.basecamp_system.generate_basecamp_display(
        user.id
    )

    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🎨 Change Theme", callback_data="change_theme")],
            [InlineKeyboardButton("🏆 View Trophies", callback_data="view_trophies")],
            [InlineKeyboardButton("📊 Basecamp Stats", callback_data="basecamp_stats")],
        ]
    )

    await update.message.reply_text(
        basecamp_display, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard
    )


async def change_theme_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle theme change requests."""
    user = update.effective_user
    logger.info(f"change_theme_handler called by user {user.id}")
    themes = engagement_engine.basecamp_system.get_available_themes()

    keyboard_buttons = []
    for theme in themes:
        keyboard_buttons.append(
            [
                InlineKeyboardButton(
                    f"{theme['emoji']} {theme['name']}",
                    callback_data=f"set_theme_{theme['id']}",
                )
            ]
        )

    keyboard = InlineKeyboardMarkup(keyboard_buttons)

    await update.callback_query.message.reply_text(
        "🎨 **Choose Your Room Theme**\n\nSelect a theme for your personal basecamp:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=keyboard,
    )


# ============================================================================
# RISK-REWARD SYSTEM HANDLERS
# ============================================================================


async def show_wager_options_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """Show wager options for risk-reward mode."""
    user = update.effective_user
    logger.info(f"show_wager_options_handler called by user {user.id}")

    # Check if player already has a wager
    wager_info = engagement_engine.risk_reward_system.get_wager_info(user.id)
    if wager_info:
        wager_display = engagement_engine.risk_reward_system.get_wager_display(user.id)
        await update.message.reply_text(wager_display, parse_mode=ParseMode.MARKDOWN)
        return

    # Show wager options
    wager_configs = engagement_engine.risk_reward_system.wager_configs

    display = "🎯 **Risk-Reward Mode**\n\nPlace a wager to multiply your XP gains!\n\n"

    keyboard_buttons = []
    for wager_type, config in wager_configs.items():
        display += (
            f"{config['emoji']} **{config['name']}**\n"
            f"   📈 {config['multiplier']}x XP Multiplier\n"
            f"   💰 {config['xp_percentage']*100}% XP Wagered\n"
            f"   📝 {config['description']}\n\n"
        )

        keyboard_buttons.append(
            [
                InlineKeyboardButton(
                    f"{config['emoji']} {config['name']}",
                    callback_data=f"place_wager_{wager_type.value}",
                )
            ]
        )

    keyboard = InlineKeyboardMarkup(keyboard_buttons)

    await update.message.reply_text(
        display, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard
    )


async def place_wager_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle wager placement."""
    query = update.callback_query
    await query.answer()
    logger.info(f"place_wager_handler called by user {update.effective_user.id}")

    user = update.effective_user
    wager_type_str = query.data.replace("place_wager_", "")

    try:
        wager_type = WagerType(wager_type_str)
        success, message = engagement_engine.risk_reward_system.place_wager(
            user.id, wager_type
        )

        await query.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
    except ValueError:
        await query.message.reply_text("❌ Invalid wager type.")


# ============================================================================
# MISSION SYSTEM HANDLERS
# ============================================================================


async def show_missions_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show player's active missions."""
    user = update.effective_user
    logger.info(f"show_missions_handler called by user {user.id}")
    mission_display = engagement_engine.mission_system.generate_mission_display(user.id)

    await update.message.reply_text(mission_display, parse_mode=ParseMode.MARKDOWN)


async def claim_mission_rewards_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """Handle mission reward claiming."""
    query = update.callback_query
    await query.answer()
    logger.info(
        f"claim_mission_rewards_handler called by user {update.effective_user.id}"
    )

    user = update.effective_user
    missions = engagement_engine.mission_system.get_player_missions(user.id)

    claimed_count = 0
    for mission_id, progress in missions.items():
        if progress["completed"] and not progress.get("claimed", False):
            success, message = engagement_engine.mission_system.claim_mission_rewards(
                user.id, mission_id
            )
            if success:
                claimed_count += 1

    if claimed_count > 0:
        await query.message.reply_text(
            f"🎉 **Claimed {claimed_count} mission rewards!**\n\nCheck your XP and inventory for new items!",
            parse_mode=ParseMode.MARKDOWN,
        )
    else:
        await query.message.reply_text(
            "❌ **No rewards to claim**\n\nComplete more missions to earn rewards!",
            parse_mode=ParseMode.MARKDOWN,
        )


# ============================================================================
# FLASH GAMES SYSTEM HANDLERS
# ============================================================================


async def show_flash_events_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show active and upcoming flash events."""
    logger.info(f"show_flash_events_handler called by user {update.effective_user.id}")
    flash_display = engagement_engine.flash_games_system.generate_flash_events_display()

    await update.message.reply_text(flash_display, parse_mode=ParseMode.MARKDOWN)


async def join_flash_event_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle joining flash events."""
    query = update.callback_query
    await query.answer()
    logger.info(f"join_flash_event_handler called by user {update.effective_user.id}")

    user = update.effective_user
    active_events = engagement_engine.flash_games_system.get_active_events()

    if not active_events:
        await query.message.reply_text(
            "❌ **No active events**\n\nCheck back later for flash events!",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    # Show available events to join
    keyboard_buttons = []
    for event in active_events:
        keyboard_buttons.append(
            [
                InlineKeyboardButton(
                    f"{event.emoji} {event.name}",
                    callback_data=f"join_event_{event.event_id}",
                )
            ]
        )

    keyboard = InlineKeyboardMarkup(keyboard_buttons)

    await query.message.reply_text(
        "⚡ **Join Flash Event**\n\nSelect an event to join:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=keyboard,
    )


# ============================================================================
# BETRAYAL CARDS SYSTEM HANDLERS
# ============================================================================


async def show_cards_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show player's betrayal cards."""
    user = update.effective_user
    logger.info(f"show_cards_handler called by user {user.id}")
    card_display = engagement_engine.betrayal_cards_system.generate_inventory_display(
        user.id
    )

    await update.message.reply_text(card_display, parse_mode=ParseMode.MARKDOWN)


async def use_card_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle card usage."""
    query = update.callback_query
    await query.answer()
    logger.info(f"use_card_handler called by user {update.effective_user.id}")

    user = update.effective_user
    inventory = engagement_engine.betrayal_cards_system.get_player_inventory(user.id)

    if not inventory:
        await query.message.reply_text(
            "❌ **No cards available**\n\nEarn cards by opening crates or completing missions!",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    # Show available cards to use
    keyboard_buttons = []
    for card_type, count in inventory.items():
        if count > 0:
            card_info = engagement_engine.betrayal_cards_system.get_card_info(
                CardType(card_type)
            )
            if card_info:
                keyboard_buttons.append(
                    [
                        InlineKeyboardButton(
                            f"{card_info['emoji']} {card_info['name']} (x{count})",
                            callback_data=f"use_card_{card_type}",
                        )
                    ]
                )

    keyboard = InlineKeyboardMarkup(keyboard_buttons)

    await query.message.reply_text(
        "🃏 **Use Betrayal Card**\n\nSelect a card to use:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=keyboard,
    )


# ============================================================================
# SHAREABLE RESULTS SYSTEM HANDLERS
# ============================================================================


async def share_result_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle sharing game results."""
    user = update.effective_user
    logger.info(f"share_result_handler called by user {user.id}")

    # For demonstration, create a sample game result
    game_result = {
        "game_id": "demo_123",
        "won": True,
        "role": "crewmate",
        "players_count": 6,
        "tasks_completed": 3,
        "xp_gained": 50,
        "mvp": False,
        "close_game": True,
    }

    share_message = engagement_engine.shareable_results_system.create_shareable_result(
        user.id, game_result["game_id"], game_result
    )

    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("📤 Share to Group", callback_data="share_to_group")],
            [
                InlineKeyboardButton(
                    "📊 View Sharing Stats", callback_data="sharing_stats"
                )
            ],
            [InlineKeyboardButton("🔥 Viral Results", callback_data="viral_results")],
        ]
    )

    await update.message.reply_text(
        share_message, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard
    )


async def show_sharing_leaderboard_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """Show sharing leaderboard."""
    logger.info(
        f"show_sharing_leaderboard_handler called by user {update.effective_user.id}"
    )
    leaderboard = (
        engagement_engine.shareable_results_system.generate_sharing_leaderboard()
    )

    await update.message.reply_text(leaderboard, parse_mode=ParseMode.MARKDOWN)


# ============================================================================
# ENGAGEMENT SUMMARY HANDLER
# ============================================================================


async def show_engagement_summary_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """Show comprehensive engagement summary."""
    user = update.effective_user
    logger.info(f"show_engagement_summary_handler called by user {user.id}")
    summary = engagement_engine.generate_engagement_summary(user.id)

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "📊 Engagement Stats", callback_data="engagement_stats"
                )
            ],
            [InlineKeyboardButton("🏆 Achievements", callback_data="achievements")],
            [InlineKeyboardButton("🎯 Quick Actions", callback_data="quick_actions")],
        ]
    )

    await update.message.reply_text(
        summary, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard
    )


# ============================================================================
# CALLBACK QUERY HANDLER
# ============================================================================


async def handle_engagement_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """Handle all engagement-related callback queries."""
    query = update.callback_query
    data = query.data
    logger.info(f"handle_engagement_callback called by user {update.effective_user.id}")
    logger.debug(f"Engagement callback data: {data}")

    try:
        if data == "change_title":
            await show_titles_handler(update, context)
        elif data == "change_theme":
            await change_theme_handler(update, context)
        elif data == "place_wager_":
            await place_wager_handler(update, context)
        elif data.startswith("place_wager_"):
            await place_wager_handler(update, context)
        elif data == "claim_missions":
            await claim_mission_rewards_handler(update, context)
        elif data == "join_flash_event":
            await join_flash_event_handler(update, context)
        elif data.startswith("join_event_"):
            # Handle joining specific event
            event_id = data.replace("join_event_", "")
            user = update.effective_user
            success, message = engagement_engine.flash_games_system.join_flash_event(
                user.id, event_id
            )
            await query.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
        elif data == "use_card":
            await use_card_handler(update, context)
        elif data.startswith("use_card_"):
            # Handle using specific card
            card_type_str = data.replace("use_card_", "")
            user = update.effective_user
            try:
                card_type = CardType(card_type_str)
                success, message = engagement_engine.betrayal_cards_system.use_card(
                    user.id, card_type, "demo_game"
                )
                await query.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
            except ValueError:
                await query.message.reply_text("❌ Invalid card type.")
        elif data == "sharing_stats":
            await show_sharing_leaderboard_handler(update, context)
        elif data == "engagement_stats":
            user = update.effective_user
            stats = engagement_engine.get_engagement_stats(user.id)
            stats_text = (
                f"📊 **Engagement Statistics**\n\n"
                f"📋 Missions Completed: {stats['missions_completed']}\n"
                f"🏆 Trophies Earned: {stats['trophies_earned']}\n"
                f"🃏 Cards Collected: {stats['cards_collected']}\n"
                f"📤 Shares Made: {stats['shares_made']}"
            )
            await query.message.reply_text(stats_text, parse_mode=ParseMode.MARKDOWN)
        else:
            await query.answer("Feature coming soon!")

    except Exception as e:
        logger.error(f"Error handling engagement callback: {e}")
        await query.answer("❌ An error occurred!")
