import asyncio
from bot.database import SessionLocal
from bot.database.models import GameSession, PlayerGameLink, Player


class GameState:
    def __init__(self, chat_id, db_session):
        self.db = db_session
        self.chat_id = chat_id
        self.game_session = None

    @classmethod
    async def create(cls, chat_id):
        db_session = SessionLocal()
        instance = cls(chat_id, db_session)
        instance.game_session = await instance._get_or_create_session()
        return instance

    async def _get_or_create_session(self):
        loop = asyncio.get_event_loop()
        session = await loop.run_in_executor(
            None,
            lambda: self.db.query(GameSession)
            .filter_by(chat_id=self.chat_id, game_type="imposter_royale")
            .first(),
        )
        if not session:
            session = GameSession(
                chat_id=self.chat_id, game_type="imposter_royale", status="waiting"
            )
            self.db.add(session)
            await loop.run_in_executor(None, self.db.commit)
        return session

    async def set_phase(self, phase):
        self.game_session.status = phase
        await asyncio.get_event_loop().run_in_executor(None, self.db.commit)

    async def get_phase(self):
        return self.game_session.status

    async def add_player(self, player_obj):
        loop = asyncio.get_event_loop()
        player_in_db = await loop.run_in_executor(
            None, lambda: self.db.query(Player).filter_by(id=player_obj.user_id).first()
        )
        if not player_in_db:
            player_in_db = Player(id=player_obj.user_id, name=player_obj.name)
            self.db.add(player_in_db)
            await loop.run_in_executor(None, self.db.commit)

        link = PlayerGameLink(
            player_id=player_in_db.id,
            session_id=self.game_session.id,
            role=player_obj.role,
        )
        self.db.add(link)
        await loop.run_in_executor(None, self.db.commit)

    async def get_all_players(self):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.db.query(Player)
            .join(PlayerGameLink)
            .filter(PlayerGameLink.session_id == self.game_session.id)
            .all(),
        )

    async def update_player_location(self, user_id, room):
        # This would require a 'location' field in PlayerGameLink or Player model
        pass

    async def update_player_status(self, user_id, status):
        loop = asyncio.get_event_loop()
        link = await loop.run_in_executor(
            None,
            lambda: self.db.query(PlayerGameLink)
            .filter_by(player_id=user_id, session_id=self.game_session.id)
            .first(),
        )
        if link:
            link.outcome = status
            await loop.run_in_executor(None, self.db.commit)

    async def log_event(self, event_type, data):
        # This would require a new table for game events
        pass

    async def add_vote(self, voter_id, target_id):
        # This would require a 'votes' table or similar
        pass

    async def get_votes(self):
        # This would require a 'votes' table or similar
        return {}

    async def clear_votes(self):
        # This would require a 'votes' table or similar
        pass
