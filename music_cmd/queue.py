import discord
from discord.ext import commands

'''
The class is for future use, currently the music queue is stored as a 2d array
'''
class MQueue(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queue = []
        self.ch = []

async def setup(bot):
    await bot.add_cog(MQueue(bot))   