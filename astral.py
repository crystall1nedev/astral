
import discord
import os
from discord.ext import commands, tasks
from support.storage import astral_storage
from support.error import astral_error, astral_exception
print(f"[bot    ] {astral_storage.get_global_str("astral", "name")}")

# console markers
success = '[√]'
error = '[x]'

#load token and owner from disk
token = astral_storage.get_global_str("astral", "token")
if token is None:
    raise astral_exception(astral_error.bot.undef_token)

# bot setup
intents = discord.Intents.default()
intents.members = True

# For safety reasons, all pings are disabled by default.
# In the future, this will be configurable via .ini, for
# now you can override this per-message.
allowed_mentions = discord.AllowedMentions(
    everyone=False, 
    users=False, 
    roles=False, 
    replied_user=False
)

bot = commands.Bot(
    intents=intents,
    allowed_mentions=allowed_mentions
)

#load cogs
cogs = astral_storage.get_global_str_list("astral", "cogs")
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

@tasks.loop(seconds=astral_storage.get_global_int("astral", "saveInterval"))
async def autosave():
    print("[storage] saving all configs to disk")
    try:
        astral_storage.save_configs_to_disk()
        print(f"[storage] saved. waiting another {astral_storage.get_global_int("astral", "saveInterval")} seconds before saving again.")
    except Exception as e:
        print(e)

@bot.event
async def on_ready():
    print(f"[bot    ] {success} Bot sucessfully initialized as {bot.user}")
    autosave.start()

@bot.event
async def on_application_command_error(ctx: discord.ApplicationContext, error: discord.DiscordException):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.respond("The used command is currently on cooldown!")
    elif isinstance(error, commands.MissingRole):
        await ctx.respond("You don't have the required role to use this command")
    else:
        raise error  # Here we raise other errors to ensure they aren't ignored

bot.run(token)
