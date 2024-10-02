from discord import Intents
from discord.ext import commands

# 올바른 인텐트 가져오기
intents = Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)
