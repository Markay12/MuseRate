import discord
from discord.ext import commands
from musicRate import musicRate

import os


client = commands.Bot(command_prefix='!', intents=discord.Intents.all())

client.add_cog(musicRate(client))


client.run("ODc1ODcyMjU4MDc2MzExNjQy.YRb1mw.bDF-qSUriAGnF7l0fYxdiDvKr1g")
