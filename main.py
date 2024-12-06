import discord
from discord import app_commands

import os

MY_GUILD = discord.Object(id=int(os.getenv("GUILD_ID")))


class Bot(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self) -> None:
        self.tree.copy_global_to(guild=MY_GUILD)
        await self.tree.sync(guild=MY_GUILD)

    async def on_ready(self):
        print(f"Logged as {self.user} (ID: {self.user.id})")
        print("--------")


intents = discord.Intents.default()
client = Bot(intents=intents)

if __name__ == '__main__':
    client.run(os.getenv("TOKEN"))
