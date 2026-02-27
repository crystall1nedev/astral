import discord
import requests
from requests.exceptions import HTTPError
from discord import option
from discord.commands import SlashCommandGroup, OptionChoice
from discord.ext import commands
from support.storage import astral_storage

class config(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Config group commands
    configGroup = SlashCommandGroup("config", "Utilities related to configuring the bot")

    ## Allows saving all configurations in memory to disk before the next scheduled autosave.
    ## Doesn't mess with the running loop at all.
    ##
    ## /config saveall
    @configGroup.command(name="saveall", description="Saves all configurations currently in memory to disk.")
    async def saveAll(self, ctx):
        try:
            msg = await ctx.respond("Preparing to save data, please do not remove MEMORY CARD™ for PLAYSTATION®2...")
            if (not astral_storage.is_caller_owner(ctx.author)):
                await msg.edit(content="You don't have permission to do that.")
            
            astral_storage.saveConfigsToDisk()
            await msg.edit(content="Saved to MEMORY CARD™ for PLAYSTATION®2 in slot 1.")
        except Exception as e:
            content = "Something went wrong while running that command."
            if astral_storage.get_global_bool("astral", "debug"):
                print("[command] roletest failed: {e}")
                content += f"\n{e}"
            await msg.edit(content=content)

    # Global group commands
    globalGroup = configGroup.create_subgroup("global", "Conigures bot-wide settings (owner-only)")
    
    ## Add or remove owners of the bot. These members can run owner-only commands.
    ## If there are no pre-existing owners, the first user to bepassed through this command will be given
    ## an "owner" title. They will need to be the one to add other owners in the future.
    ## 
    ## /config global owner {add/remove} {user}
    @globalGroup.command(name="owner",description=f"Add an owner to the owner list (owner-only)")
    @option("operation",type=str,choices=[OptionChoice("Add role to allowlist", "add"), OptionChoice("Remove role from allowlist", "remove")],description="What should be done here?",required=True)
    @option("user", type=discord.Member, description="The user to add as an owner", required=True)
    async def addOwner(self, ctx, operation: str, user: discord.Member):
        try:
            msg = await ctx.respond(f"Preparing to add {user.mention} as an owner...")
            owners = astral_storage.get_global_int_list("astral", "owners")
            if ctx.author.id not in owners and len(owners) > 0:
                await msg.edit(content="You don't have permission to do that.")
                return
            
            if user.id in owners and operation == "add":
                if ctx.author.id == user.id:
                    await msg.edit(content=f"You already own me.")
                    return 
                await msg.edit(content=f"***{user.mention}*** already owns me.")
                return
            
            if user.id not in owners and operation == "remove":
                await msg.edit(content=f"***{user.mention}*** doesn't already own me.")
                return
            
            owners.append(user.id)
            astral_storage.set_global_list("astral", "owners", owners)
            await msg.edit(content=f"Added ***{user.mention}*** as an owner for {astral_storage.get_global_str("astral", "name")}.")
        except Exception as e:
            msg = "Something went wrong while running that command."
            if astral_storage.get_global_bool("debug"):
                print("[command] addOwner failed: {e}")
                msg += f"\n{e}"
            await msg.edit(content=msg)

    @globalGroup.command(name="escpos",description=f"Configure ESC/POS settings (owner-only)")
    @option("ip",type=str,description="The IP address of the ESC/POS printer to connect to.",required=False)
    @option("port",type=int,description="The port of the ESC/POS printer to connect to.",required=False)
    @option("profile",type=str,description="The profile of the ESC/POS printer, usually the model name.",required=False)
    @option("enable_multitone",type=bool,description="Should multitone printing support be available to users?",required=False)
    @option("verbosity",type=bool,description="Should messages update with each action in the ESC/POS pipeline?",required=False)
    async def configureEscpos(self, ctx, ip: str = None, port: int = None, profile: str = None, multitone: bool = None, verbosity: bool = None):
        try:
            msg = await ctx.respond("Configuring ESC/POS functionality...")
            if (not astral_storage.is_caller_owner(ctx.author)):
                await msg.edit(content="You don't have permission to do that.")
            
            content = ""
            if ip is not None:
                val = astral_storage.get_global_str("escpos", "ip")
                if val is not None and ip == val:
                    content += f"IP address remains set to {ip}\n"
                else:
                    astral_storage.set_global_str("escpos", "ip", ip)
                    content += f"IP address has been set to {ip}\n"
            if port is not None:
                val = astral_storage.get_global_str("escpos", "port")
                if val is not None and port == val:
                    content += f"Port remains set to {ip}\n"
                else:
                    astral_storage.set_global_int("escpos", "port", port)
                    content += f"Port has been set to {port}\n"
            if profile is not None:
                val = astral_storage.get_global_str("escpos", "profile")
                if val is not None and profile == val:
                    content += f"Profile remains set to {ip}\n"
                else:
                    astral_storage.set_global_str("escpos", "profile", profile)
                    content += f"Profile has been set to {profile}\n"
            if multitone is not None:
                val = astral_storage.get_global_str("escpos", "multitone")
                if val is not None and multitone == val:
                    content += f"Multitone remains {"enabled" if multitone else "disabled"}\n"
                else:
                    astral_storage.set_global_bool("escpos", "multitone", multitone)
                    content += f"Multitone is {"enabled" if multitone else "disabled"}\n"
            if verbosity is not None:
                val = astral_storage.get_global_str("escpos", "verbosity")
                if val is not None and verbosity == val:
                    content += f"Discord verbosity remains set to {ip}\n"
                else:
                    astral_storage.set_global_bool("escpos", "verbosity", verbosity)
                    content += f"Discord verbosity {"enabled" if multitone else "disabled"}\n"
            await msg.edit(content=f"{content}\nYour changes have been saved.")
        except Exception as e:
            content = "Something went wrong while running that command."
            if astral_storage.get_global_bool("astral", "debug"):
                print("[command] roletest failed: {e}")
                content += f"\n{e}"
            await msg.edit(content=content)

    # Commands related to the management of ESC/POS functionality
    escposGroup = configGroup.create_subgroup("escpos", "Configure settings related to printing on an ESC/POS printer")

    ## (Per-server) Configures the role(s) that are allowed to use ESC/POS commands that cause actual printing.
    ## This can only be configured by the owners of the bot.
    ##
    ## /config escpos role {add/remove} {role}
    @escposGroup.command(name="role",description="Configure what roles can and cannot access ESC/POS functionality.")
    @option("operation",type=str,choices=[OptionChoice("Add role to allowlist", "add"), OptionChoice("Remove role from allowlist", "remove")],description="What should be done here?",required=False)
    @option("role", type=discord.Role, description="The role to act upon", required=False)
    async def escposRolesFromServer(self, ctx, operation: str = None, role: discord.Role = None): 
        try:
            roles = astral_storage.get_server_int_list(ctx.guild.id, "allowedroles", "escpos")
            if roles is None: roles = []
            if operation is None and role is None:
                msg = await ctx.respond("Getting ESC/POS roles...")
                
                content = "The following roles can interact with the printer: "
                rolesList = []
                for roleid in roles:
                    roleToMention = ctx.guild.get_role(roleid)
                    if roleToMention: 
                        rolesList.append(roleToMention.mention)

                content += ", ".join(rolesList)
                await msg.edit(content=content)
                return
            
            if operation is None:
                await ctx.respond("You need to supply what to do with the role.")
                return
            
            if role is None:
                await ctx.respond(f"You need to supply the role to {operation}.")
                return


            msg = await ctx.respond(f"Preparing to {operation} {role.mention} to escpos roles...")
            if (not astral_storage.is_caller_owner(ctx.author)):
                await msg.edit(content="You don't have permission to do that.")
            
            if role.id in roles and operation == "add":
                await msg.edit(content=f"Users with ***{role.mention}*** can already interact with the ESC/POS printer.")
                return
            
            if role.id not in roles and operation == "remove":
                await msg.edit(content=f"Users with ***{role.mention}*** are already unable with the ESC/POS printer.")
                return

            if operation == "add":    roles.append(role.id)
            if operation == "remove": roles.remove(role.id)
            astral_storage.set_server_list(ctx.guild.id, "allowedroles", "escpos", roles)
            await msg.edit(content=f"Users with ***{role.mention}*** can {"now" if operation == "add" else "no longer"} interact with the ESC/POS printer.")
        except Exception as e:
            content = "Something went wrong while running that command."
            if astral_storage.get_global_bool("astral", "debug"):
                print("[command] escposRolesFromServer failed: {e}")
                content += f"\n{e}"
            await msg.edit(content=content)

    # Cartel commands
    cartelGroup = configGroup.create_subgroup("cartel", "Configure settings related to the cartel")

def setup(bot): # this is called by Pycord to setup the cog
    bot.add_cog(config(bot)) # add the cog to the bot