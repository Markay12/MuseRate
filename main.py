import discord
from discord.ext import commands
from musicRate import musicRate

import os


client = commands.Bot(command_prefix="//", intents=discord.Intents.all())

client.add_cog(musicRate(client))

client.run(os.environ['TOKEN'])
