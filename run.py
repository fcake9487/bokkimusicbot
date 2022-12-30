import discord
from discord.ext import commands
import json, os

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', activity = discord.Game('Guitar Hero'),intents=intents)

configFile = open("config.json","r")
configData = json.load(configFile)

@bot.event
async def on_ready():
    print(f'{bot.user} has activated!')

    for file in os.listdir('./music_cmd'):
        if file.endswith('.py'):
            await bot.load_extension(f'music_cmd.{file[:-3]}') #it takes me fuckin eternal time(maybe) to do this shit, fuck discord.py
    
    
bot.run(configData["botinfo"]["token"])


