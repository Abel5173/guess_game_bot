from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from bot.handlers.pulse_code_handlers import (
    start_pulse_code,
    guess_pulse_code,
    mind_link,
    desperation_gambit,
    pulse_code_status,
    end_pulse_code,
    feedback,
    join_pulse_code,
    leave_pulse_code,
    pulse_code_players,
    start_dual_operative_game,
    start_triple_threat_game,
    handle_pulse_callback,
    join_pvp,
    set_code,
    pvp_guess,
    pvp_status,
    end_pvp,
    join_group_ai,
    start_group_ai,
    group_guess,
    group_status,
    end_group_ai,
    join_team_a,
    join_team_b,
    set_team_code,
    start_group_pvp,
    team_guess,
    team_status,
    end_group_pvp,
)
from bot.handlers.topic_handlers import (
    create_topic_game_handler,
    show_available_games_handler,
    topic_message_handler,
    callback_query_handler as topic_callback_handler,
)
from bot.handlers.analytics_handlers import (
    show_player_stats,
    show_team_stats,
    show_leaderboard,
    show_session_leaderboard,
    show_chat_stats,
    show_global_leaderboard,
    show_recent_games,
    show_analytics_menu,
    handle_analytics_callback,
)
from bot.handlers.engagement_handlers import (
    show_engagement_summary_handler,
    show_basecamp_handler,
    show_missions_handler,
    show_flash_events_handler,
    show_cards_handler,
    handle_engagement_callback,
)
from bot.handlers.ai_handlers import (
    ai_status_handler,
    ai_personas_handler,
    ai_detective_handler,
    ai_chaos_handler,
    ai_lore_handler,
    ai_task_handler,
    handle_ai_callback,
)
from bot.handlers.game_selection_handlers import handle_game_selection_callback
from bot.handlers.player_handlers import show_profile, show_leaderboard
from main import (
    start_private,
    help_command,
    about_command,
    button_click,
    handle_discussion,
    error_handler,
)


def register_handlers(application: Application, start_game_func):
    """Registers all the handlers for the bot."""

    # Core commands
    application.add_handler(CommandHandler("start", start_private))
    application.add_handler(CommandHandler("startgame", start_game_func))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("about", about_command))
    application.add_handler(CommandHandler("profile", show_profile))
    application.add_handler(CommandHandler("leaderboard", show_leaderboard))

    # Pulse Code commands
    application.add_handler(CommandHandler("start_pulse_code", start_pulse_code))
    application.add_handler(CommandHandler("guess", guess_pulse_code))
    application.add_handler(CommandHandler("mind_link", mind_link))
    application.add_handler(CommandHandler("desperation_gambit", desperation_gambit))
    application.add_handler(CommandHandler("my_stress", pulse_code_status))
    application.add_handler(CommandHandler("end_pulse_code", end_pulse_code))
    application.add_handler(CommandHandler("feedback", feedback))
    application.add_handler(CommandHandler("join_pulse_code", join_pulse_code))
    application.add_handler(CommandHandler("leave_pulse_code", leave_pulse_code))
    application.add_handler(CommandHandler("pulse_code_players", pulse_code_players))
    application.add_handler(
        CommandHandler("start_dual_operative_game", start_dual_operative_game)
    )
    application.add_handler(
        CommandHandler("start_triple_threat_game", start_triple_threat_game)
    )
    # PvP commands
    application.add_handler(CommandHandler("join_pvp", join_pvp))
    application.add_handler(CommandHandler("set_code", set_code))
    application.add_handler(CommandHandler("pvp_guess", pvp_guess))
    application.add_handler(CommandHandler("pvp_status", pvp_status))
    application.add_handler(CommandHandler("end_pvp", end_pvp))

    # Group vs. AI commands
    application.add_handler(CommandHandler("join_group_ai", join_group_ai))
    application.add_handler(CommandHandler("start_group_ai", start_group_ai))
    application.add_handler(CommandHandler("group_guess", group_guess))
    application.add_handler(CommandHandler("group_status", group_status))
    application.add_handler(CommandHandler("end_group_ai", end_group_ai))

    # Group vs. Group commands
    application.add_handler(CommandHandler("join_team_a", join_team_a))
    application.add_handler(CommandHandler("join_team_b", join_team_b))
    application.add_handler(CommandHandler("set_team_code", set_team_code))
    application.add_handler(CommandHandler("start_group_pvp", start_group_pvp))
    application.add_handler(CommandHandler("team_guess", team_guess))
    application.add_handler(CommandHandler("team_status", team_status))
    application.add_handler(CommandHandler("end_group_pvp", end_group_pvp))

    # Topic-based game commands
    application.add_handler(CommandHandler("creategame", create_topic_game_handler))
    application.add_handler(CommandHandler("joingames", show_available_games_handler))

    # Analytics commands
    application.add_handler(CommandHandler("my_stats", show_player_stats))
    application.add_handler(CommandHandler("team_stats", show_team_stats))
    application.add_handler(CommandHandler("leaderboard", show_leaderboard))
    application.add_handler(CommandHandler("chatstats", show_chat_stats))
    application.add_handler(CommandHandler("global", show_global_leaderboard))
    application.add_handler(CommandHandler("recent", show_recent_games))
    application.add_handler(CommandHandler("analytics", show_analytics_menu))

    # Engagement commands
    application.add_handler(CommandHandler("basecamp", show_basecamp_handler))
    application.add_handler(CommandHandler("missions", show_missions_handler))
    application.add_handler(CommandHandler("flash", show_flash_events_handler))
    application.add_handler(CommandHandler("cards", show_cards_handler))
    application.add_handler(
        CommandHandler("engagement", show_engagement_summary_handler)
    )

    # AI commands
    application.add_handler(CommandHandler("ai", ai_status_handler))
    application.add_handler(CommandHandler("aistatus", ai_status_handler))
    application.add_handler(CommandHandler("aipersonas", ai_personas_handler))
    application.add_handler(CommandHandler("aidetective", ai_detective_handler))
    application.add_handler(CommandHandler("aichaos", ai_chaos_handler))
    application.add_handler(CommandHandler("ailore", ai_lore_handler))
    application.add_handler(CommandHandler("aitask", ai_task_handler))

    # Callback Query Handlers
    application.add_handler(CallbackQueryHandler(handle_game_selection_callback, pattern="^select_game_"))
    application.add_handler(CallbackQueryHandler(handle_pulse_callback, pattern="^pulse_"))
    application.add_handler(
        CallbackQueryHandler(topic_callback_handler, pattern="^topic_")
    )
    application.add_handler(
        CallbackQueryHandler(handle_analytics_callback, pattern="^analytics_")
    )
    application.add_handler(
        CallbackQueryHandler(handle_engagement_callback, pattern="^engagement_")
    )
    application.add_handler(CallbackQueryHandler(handle_ai_callback, pattern="^ai_"))
    application.add_handler(CallbackQueryHandler(button_click))

    # Message Handlers
    application.add_handler(
        MessageHandler(filters.TEXT & filters.ChatType.GROUPS, handle_discussion)
    )

    # Error Handler
    application.add_error_handler(error_handler)
