import discord
from discord import app_commands
from discord.app_commands import guilds
from dotenv import load_dotenv

import os
import asyncio

load_dotenv()
MY_GUILD = discord.Object(id=int(os.getenv("GUILD_ID")))

class Bot(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.bg_task = None
        self.tree = app_commands.CommandTree(self)
        self.data = None
        self.guild = None
        self.logs = None

        # initialize server stats
        self.cMember = None
        self.cUser = None
        self.cBot = None
        self.numOfBot = None
        self.numOfMember = None
        self.last_update = None

        #initialize functionality channel
        self.welcomeChannel = None

    async def setup_hook(self):
        self.tree.clear_commands(guild=MY_GUILD)
        await self.tree.sync()
        # self.tree.copy_global_to(guild=MY_GUILD)
        # await self.tree.sync(guild=MY_GUILD)

    async def on_ready(self):
        print(f"Logged as {self.user} (ID: {self.user.id})")
        self.guild = discord.utils.get(self.guilds, id=int(os.getenv("GUILD_ID")))
        self.logs = discord.utils.get(self.guild.channels, id=int(os.getenv("LOGS")))
        self.cMember = discord.utils.get(self.guild.channels, id=int(os.getenv("MEMBER_COUNT")))
        self.cUser = discord.utils.get(self.guild.channels, id=int(os.getenv("USER_COUNT")))
        self.cBot = discord.utils.get(self.guild.channels, id=int(os.getenv("BOT_COUNT")))
        self.welcomeChannel = discord.utils.get(self.guild.channels, id=int(os.getenv("WELCOME_CHANNEL")))

        if self.guild:
            print(f"Connected to guild: {self.guild.name}")
            if self.welcomeChannel:
                print(f"Found welcome channel: {self.welcomeChannel}")
            if self.cMember and self.cUser and self.cBot:
                print(f"Found all stats channels: {self.cMember}, {self.cUser}, {self.cBot}")

        print("--------")
        print("System: Creating background task...")
        self.bg_task = self.loop.create_task(self.update_stats_channel_periodically())
        bgTaskText = "System: Created background task, server stats will be updated every 5 minutes"
        print(bgTaskText)
        await self.system_response(bgTaskText)

    async def system_response(self, text):
        await self.logs.send(text)

    async def on_member_join(self, member):

        await self.logs.send(f"A person has joined")

    async def on_member_remove(self, member):

        await self.logs.send(f"A person has removed")

    async def update_stats_channel_periodically(self):
        while True:
            await asyncio.sleep(60*5)
            self.numOfBot = sum(1 for member in self.guild.members if member.bot)
            self.numOfMember = len(self.guild.members)
            if self.cMember:
                await self.cMember.edit(name=f"Members: {self.numOfMember}")
            if self.cUser:
                await self.cUser.edit(name=f"Users: {self.numberOfMember - self.numOfBot}")
            if self.cBot:
                await self.cBot.edit(name=f"Bots: {self.numOfBot}")



intents = discord.Intents.all()
client = Bot(intents=intents)

def has_permission(user, required_roles):
    user_roles = [role.name for role in user.roles]

    if isinstance(required_roles, list):
        for role in required_roles:
            if role in user_roles:
                return True

        return False


@client.tree.command()
async def set_nickname(interaction: discord.Interaction, user: discord.User, nickname: str):
    """Chỉ có Dev và Admin mới có thể dùng lệnh này"""
    guild = interaction.guild
    logs = guild.get_channel(int(os.getenv("LOGS")))
    member = guild.get_member(user.id)

    if not has_permission(interaction.user, ["Dev", "Administrator"]):
        await interaction.response.send_message("Bạn không có quyền sử dụng lệnh này!", ephemeral=True)
        await logs.send(f"System: {interaction.nick} is trying to use /set_nickname without permission.")
        return

    if not member:
        await interaction.response.send_message("Không tìm thấy người dùng trong server.")
        await logs.send(f"Command - set_nickname: Cannot find {user} in the command")
        return

    highest_role = sorted(member.roles, key=lambda role: role.position, reverse=True)[0]

    nick = f"{highest_role.name}| {nickname}"


    try:
        await member.edit(nick=nick)
        await interaction.response.send_message(f"Đã thay đổi nickname của {user} thành {nickname}!", ephemeral=True)
        await logs.send(f"Command - set_nickname: {user}'s nick has been changed successfully")
    except discord.Forbidden:
        await interaction.response.send_message("Tôi không có quyền để thay đổi nickname", ephemeral=True)
        await logs.send(f"System: Lack of permission.")

if __name__ == '__main__':
    client.run(os.getenv("TOKEN"))
