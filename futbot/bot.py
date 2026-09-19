from __future__ import annotations

import logging

import discord
from discord.ext import commands

from futbot.branding import BOT_ACTIVITY, BOT_NAME, BOT_USERNAME_FALLBACK
from futbot.config import Settings, load_settings
from futbot.cogs.market import MarketCog
from futbot.db import Store
from futbot.market.service import MarketService

logger = logging.getLogger(__name__)


class FutBot(commands.Bot):
    def __init__(self, settings: Settings, store: Store, market: MarketService) -> None:
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)
        self.settings = settings
        self.store = store
        self.market = market

    async def setup_hook(self) -> None:
        await self.add_cog(MarketCog(self, self.settings, self.store, self.market))
        if self.settings.discord_guild_id:
            guild = discord.Object(id=self.settings.discord_guild_id)
            self.tree.copy_global_to(guild=guild)
            synced = await self.tree.sync(guild=guild)
            logger.info("Synced %s guild commands", len(synced))
        else:
            synced = await self.tree.sync()
            logger.info("Synced %s global commands", len(synced))

    async def on_ready(self) -> None:
        logger.info("Logged in as %s (%s)", self.user, self.user.id if self.user else "?")
        if self.user:
            invite = discord.utils.oauth_url(
                self.user.id,
                permissions=discord.Permissions(
                    send_messages=True,
                    embed_links=True,
                    attach_files=True,
                    read_message_history=True,
                    add_reactions=True,
                    use_application_commands=True,
                ),
                scopes=("bot", "applications.commands"),
            )
            logger.info("Invite URL: %s", invite)
        guilds = list(self.guilds)
        if guilds:
            logger.info("Connected to %s guild(s): %s", len(guilds), ", ".join(g.name for g in guilds))
        else:
            logger.warning("Bot is not in any Discord server yet. Use the invite URL above.")
        for guild in guilds:
            self.tree.copy_global_to(guild=guild)
            synced = await self.tree.sync(guild=guild)
            logger.info("Synced %s commands to %s", len(synced), guild.name)
        await self._apply_identity()
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name=BOT_ACTIVITY,
            )
        )

    async def on_guild_join(self, guild: discord.Guild) -> None:
        logger.info("Joined guild %s (%s) — syncing slash commands", guild.name, guild.id)
        self.tree.copy_global_to(guild=guild)
        synced = await self.tree.sync(guild=guild)
        logger.info("Synced %s commands to %s", len(synced), guild.name)
        await self._nick_guild(guild)

    async def _apply_identity(self) -> None:
        if self.user and self.user.name not in {BOT_NAME, BOT_USERNAME_FALLBACK}:
            for candidate in (BOT_NAME, BOT_USERNAME_FALLBACK):
                try:
                    await self.user.edit(username=candidate)
                    logger.info("Discord username set to %s", candidate)
                    break
                except discord.HTTPException as exc:
                    logger.warning("Could not set username %s: %s", candidate, exc)
        for guild in self.guilds:
            await self._nick_guild(guild)

    async def _nick_guild(self, guild: discord.Guild) -> None:
        me = guild.me
        if me is None or me.nick == BOT_NAME:
            return
        try:
            await me.edit(nick=BOT_NAME)
            logger.info("Nickname in %s set to %s", guild.name, BOT_NAME)
        except discord.HTTPException as exc:
            logger.warning("Could not set nickname in %s: %s", guild.name, exc)

    async def close(self) -> None:
        await self.market.aclose()
        self.store.close()
        await super().close()


def build_bot(settings: Settings | None = None) -> FutBot:
    settings = settings or load_settings()
    store = Store(settings.database_path)
    market = MarketService(game_year=settings.game_year, cache_ttl=min(60, settings.poll_interval_seconds))
    return FutBot(settings, store, market)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    settings = load_settings()
    if not settings.discord_token:
        raise SystemExit(
            "DISCORD_TOKEN fehlt. Kopiere .env.example nach .env und setze den Bot-Token."
        )
    bot = build_bot(settings)
    bot.run(settings.discord_token)
