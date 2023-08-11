import discord
import requests
import dotenv
import os
import cpuinfo
import random
from requests.exceptions import HTTPError
from discord.commands import SlashCommandGroup
from discord.ext import commands
from discord import Option

#load basic bot info from disk
dotenv.load_dotenv()
botVersion = "1.0.1"
botVersionDate = "March 22 2023"
botName = str(os.getenv("botName"))

class fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    funGroup = SlashCommandGroup("fun", "Various little commands of dubious utility")

    @funGroup.command(name="kiss",description="kiss someone (girlkissing preferred)")
    async def ping(
        self, 
        ctx,
        member: Option(discord.Member, "person to be kissed")
    ): 
        randomNum = random.randint(0, 2)
        match randomNum:
            case 0:
                await ctx.respond(f"*{ctx.author.name}*, you kiss *{member.name}*.")
            case 1:
                await ctx.respond(f"*{ctx.author.name}*, you take *{member.name}* into your arms for a passionate kiss.")
            case 2:
                await ctx.respond(f"*{ctx.author.name}*, you lock eyes with *{member.name}*, then lean in for a kiss.")

    @funGroup.command(name="ping",description="i sure wonder how slow the bot is today!")
    async def ping(self, ctx): 
        await ctx.respond(f"latency was {round(self.bot.latency * 1000)}ms, have a stellar day")

    @funGroup.command(name="about",description=f"Prints information about {botName}")
    async def about(self, ctx): 
        await ctx.defer()
        await ctx.respond(f"*{botName}* {botVersion} ({botVersionDate})\nHost CPU: {cpuinfo.get_cpu_info()['brand_raw']} ({cpuinfo.get_cpu_info()['arch']})\nHost Python: {cpuinfo.get_cpu_info()['python_version']}")

def setup(bot):
    bot.add_cog(fun(bot))