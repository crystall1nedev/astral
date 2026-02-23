from support.storage import astralStorage
import discord
import os
from discord.ext import commands

storage = astralStorage

print(f"[bot    ] {storage.getGlobalOption("name")}")

# console markers
success = '[√]'
error = '[x]'

#load token and owner from disk
token = storage.getGlobalOption("token")

# bot setup
intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(intents=intents)

#load cogs
cogs = list(map(str.strip, storage.getGlobalOption("cogs").split(",")))
if cogs is None:
    cogs = ['osuUtils', 'fun', 'lookupUtils']
if "all" in cogs:
    cogs = os.listdir("cogs")
    for file in cogs:
        if ".py" not in file:
            cogs.remove(file) 
for cog in cogs:
    print(f"[bot    ] loading cog {cog}")
    bot.load_extension(f'cogs.{cog}')

@bot.event
async def on_ready():
    print(f"[bot    ] {success} Bot sucessfully initialized as {bot.user}")

bot.run(token)
