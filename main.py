import discord
from discord import app_commands
from discord.app_commands import guilds
from dotenv import load_dotenv

import os
import asyncio
import sqlite3

load_dotenv()
MY_GUILD = discord.Object(id=int(os.getenv("GUILD_ID")))

# support function
def has_permission(user, required_roles):
    user_roles = [role.name for role in user.roles]

    if isinstance(required_roles, list):
        for role in required_roles:
            if role in user_roles:
                return True

        return False
    
def update_data(member_id, number_no, join_date, member_realname, member_name, member_credit, member_level):
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    
    cursor.execute("""
                   INSERT INTO members (id, numberno, join_date, realname, name, credit, level)
                   VALUES (?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(id) DO UPDATE SET
                        name = ?,
                        credit = ?,
                        level = ?
""", (member_id, number_no, join_date, member_realname, member_name, member_credit, member_level, member_name, member_credit, member_level))
    conn.commit()
    conn.close()

def member_exist(member_id):
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM members WHERE id = ? ", (member_id,))
    result = cursor.fetchone()

    conn.close()

    return result is not None

def create_db():
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()

    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS members (
                        id INTEGER PRIMARY KEY,
                        numberno INTEGER,
                        join_date DATE,
                        realname TEXT,
                        name TEXT,
                        credit INTEGER DEFAULT 0,
                        level INTEGER DEFAULT 1
                   )
                   """)
    conn.commit()
    conn.close()

# create_db()

class Bot(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.bg_task = None
        self.tree = app_commands.CommandTree(self)
        self.data = None
        self.guild = None

        # initialize server stats
        self.cMember = None
        self.cUser = None
        self.cBot = None
        self.numOfBot = None
        self.numOfMember = None
        self.last_update = None

        #initialize functionality channel
        self.welcomeChannel = None
        self.ruleChannel = None
        self.pickRoleChannel = None

    async def setup_hook(self):
        # self.tree.clear_commands(guild=MY_GUILD)
        # await self.tree.sync()
        self.tree.copy_global_to(guild=MY_GUILD)
        await self.tree.sync(guild=MY_GUILD)

    async def on_ready(self):
        print(f"Logged as {self.user} (ID: {self.user.id})")
        self.guild = discord.utils.get(self.guilds, id=int(os.getenv("GUILD_ID")))
        self.cMember = discord.utils.get(self.guild.channels, id=int(os.getenv("MEMBER_COUNT")))
        self.cUser = discord.utils.get(self.guild.channels, id=int(os.getenv("USER_COUNT")))
        self.cBot = discord.utils.get(self.guild.channels, id=int(os.getenv("BOT_COUNT")))
        self.welcomeChannel = discord.utils.get(self.guild.channels, id=int(os.getenv("WELCOME_CHANNEL")))
        self.ruleChannel = discord.utils.get(self.guild.channels, id=int(os.getenv("RULE_CHANNEL")))
        self.pickRoleChannel = discord.utils.get(self.guild.channels, id=int(os.getenv("PICK_ROLE")))

        if self.guild:
            print(f"Connected to guild: {self.guild.name}")
            if self.welcomeChannel:
                print(f"Found welcome channel: {self.welcomeChannel}")
            if self.ruleChannel:
                print(f"Found rule channel: {self.ruleChannel}")
            if self.pickRoleChannel:
                print(f"Found pick role channel: {self.pickRoleChannel}")
            if self.cMember and self.cUser and self.cBot:
                print(f"Found all stats channels: {self.cMember}, {self.cUser}, {self.cBot}")

        print("--------")
        try:
            print("System: Creating background task...")
            self.bg_task = self.loop.create_task(self.update_stats_channel_periodically())
            bgTaskText = "System: Created background task, server stats will be updated every 5 minutes"
            print(bgTaskText)
        except Exception as e:
            print("System: Failed to create background task...\nError:", e)

    async def on_member_join(self, member: discord.Member):
        civilRole = discord.utils.get(self.guild.roles, name="Civilian")
        if not member_exist(member.id):
            embed = discord.Embed(
                    colour=discord.Colour.dark_teal(),
                    title=f'Welcome, {member.display_name} joined Xenia!',
                    description=f'Chào mừng bạn đã đến với chúng tôi<3.\nĐừng quên đọc qua luật {self.ruleChannel.mention} để không bị ban ngoài ý muốn nhé<3.\nVà đồng thời nhớ pick role {self.pickRoleChannel.mention} để có thể tham gia vào nhiều vùng khác nhau<3'
                )
            embed.set_footer(text=f"Thank you! Enjoy your journey ❤️")
        else:
            embed = discord.Embed(
                colour=discord.Colour.dark_teal(),
                title=f'Welcome back, {member.display_name}!',
                description=f'Chào mừng bạn quay trở lại với chúng tôi.\nĐừng quên đọc qua luật {self.ruleChannel.mention} để không bị ban ngoài ý muốn nhé<3.\nVà đồng thời nhớ pick role {self.pickRoleChannel.mention} để có thể tham gia vào nhiều vùng khác nhau<3'
            )
            embed.set_footer(text=f"Thank you! Continue our journey 🎊")
        try:
            await member.add_roles(civilRole)
            highest_role = sorted(member.roles, key=lambda role: role.position, reverse=True)[0]
            await member.edit(nick=f"{highest_role}| {member.display_name}")
            update_data(member.id, len(self.guild.members), member.joined_at, member.name, member.nick, 0, 1)
            await self.welcomeChannel.send(embed=embed)
        except discord.Forbidden:
            print("System: Bot does not have enough permissions.")
        except discord.HTTPException as e:
            if e.status == 429:
                print("System: Bot is overloading...")


    async def on_member_remove(self, member: discord.Member):
        embed = discord.Embed(
            colour=discord.Colour.dark_teal(),
            title=f'{member.display_name} has left!',
            description=f'{member.display_name} đã rời đi bỏ lại chúng ta:( hi vọng sẽ gặp lại cậu ấy một ngày không xa. . .'
        )
        embed.set_footer(text=f"Thank you! See you soon 😊")
        await self.welcomeChannel.send(embed=embed)

    async def update_stats_channel_periodically(self):
        while True:
            self.numOfBot = sum(1 for member in self.guild.members if member.bot)
            self.numOfMember = len(self.guild.members)
            if self.cMember:
                await self.cMember.edit(name=f"Members: {self.numOfMember}")
            if self.cUser:
                await self.cUser.edit(name=f"Users: {self.numOfMember - self.numOfBot}")
            if self.cBot:
                await self.cBot.edit(name=f"Bots: {self.numOfBot}")
            await asyncio.sleep(60*5)



intents = discord.Intents.all()
client = Bot(intents=intents)



@client.tree.command()
async def set_nickname(interaction: discord.Interaction, user: discord.User, nickname: str):
    """Chỉ có Dev và Admin mới có thể dùng lệnh này"""
    guild = interaction.guild
    member = guild.get_member(user.id)

    if not has_permission(interaction.user, ["Dev", "Administrator"]):
        await interaction.response.send_message("Bạn không có quyền sử dụng lệnh này!", ephemeral=True)
        return

    if not member:
        await interaction.response.send_message("Không tìm thấy người dùng trong server.")
        return

    highest_role = sorted(member.roles, key=lambda role: role.position, reverse=True)[0]

    nick = f"{highest_role.name}| {nickname}"


    try:
        await member.edit(nick=nick)
        await interaction.response.send_message(f"Đã thay đổi nickname của {user} thành {nickname}!", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message("Tôi không có quyền để thay đổi nickname", ephemeral=True)


if __name__ == '__main__':
    client.run(os.getenv("TOKEN"))
