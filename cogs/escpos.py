import os
import configparser
from pathlib import Path
from io import BytesIO

import requests
import discord
from discord.commands import SlashCommandGroup
from discord.ext import commands
from discord import option
from escpos.printer import Network
from PIL import Image
from PIL import ImageEnhance

from support.multitone import main as multitoneImage
from support.storage import astral_storage
from support.error import astral_error, astral_exception

class escpos(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.supported_pil_image_types = tuple(ex for ex, f in Image.registered_extensions().items() if f in Image.OPEN)

        # Don't worry about the None here, it's set later when commands are run
        self.allowed_role_ids     = None 
        self.allowed_user_ids     = None 
        self.verbosity_to_discord = None
        self.printer_ip           = None
        self.printer_port         = None
        self.printer_profile      = None
        self.enable_multitone     = None

    # This cog supports changing settings without needing the bot to restart.
    # In order to handle that, __init__ and each command checks back here to 
    # ensure that the command is able to be run.
    async def verify_configuration_valid(self, ctx = None) -> bool:
        ESCPOS_CHECKS = [
            (astral_error.escpos.undef_ip, "printer_ip", lambda: astral_storage.get_global_str("escpos", "ip"), None),         
            (astral_error.escpos.undef_port, "printer_port",
             lambda: astral_storage.get_global_int("escpos", "port"), 9100),
            (astral_error.escpos.undef_profile, "printer_profile",
             lambda: astral_storage.get_global_str("escpos", "profile"), None),
            (astral_error.escpos.undef_verbosity, "verbosity_to_discord",
             lambda: astral_storage.get_global_bool("escpos", "verbosity"), False),
            (astral_error.escpos.undef_multitone, "enable_multitone",
             lambda: astral_storage.get_global_bool("escpos", "multitone"), False),
        ]

        if ctx is not None:
            ESCPOS_CHECKS += [
                (astral_error.escpos.undef_server, "allowed_role_ids",
                lambda ctx: astral_storage.get_server_int_list(ctx.guild.id, "allowedroles", "escpos"), None),
                (astral_error.escpos.undef_server, "allowed_user_ids",
                lambda ctx: astral_storage.get_server_int_list(ctx.guild.id, "allowedusers", "escpos"), None),
            ]

        errors_with_config = astral_storage.issue_with_configuration_present(
            self,
            ESCPOS_CHECKS,
            ctx
        )

        # errors_with_config will always only contain critical errors
        # so we can make a decent amount of assumptions here
        if errors_with_config is not None:
            print(f"[escpos ] [print] ESC/POS cog can't continue:")
            for error in errors_with_config:
                print(f"[escpos ] [print] - {error.value}")

            if ctx is not None:
                # server skill issue
                if self.allowed_role_ids is None and self.allowed_user_ids is None and len(errors_with_config) == 2:
                    await ctx.respond("ESC/POS isn't properly set up in this server, make sure roles have been added with /config escpos roles and try again.")
                    return False
                
                elif astral_error.escpos.undef_server not in errors_with_config:
                    content = "ESC/POS isn't properly set up right now"
                    if self.verbosity_to_discord:
                        content += ":\n"
                        for error in errors_with_config:
                            content += f"{error}: {error.value}\n"
                        await ctx.respond(content=content)
                        return False
                    
                    await ctx.respond("ESC/POS isn't properly set up right now, try again later.")
                    return False
        
        return True


    def parse_paper_status(self, status):
        print(f"[escpos ] [parse_paper_status] Received paper status: {status}")
        if status == 0:
            return "There is no paper"
        elif status == 1:
            return "The paper is almost out"
        elif status == 2:
            return "There is plenty of paper"
        else:
            return "Unknown Status"

    def calculate_brightness(self, image):
        greyscale_image = image.convert('L')
        histogram = greyscale_image.histogram()
        pixels = sum(histogram)
        brightness = scale = len(histogram)

        for index in range(0, scale):
            ratio = histogram[index] / pixels
            brightness += ratio * (-scale + index)

        return 1 if brightness == 255 else brightness / scale

    def calculate_brightness_enhancement(self, brightness, max_enhancement=5):
        """
        Calculate how much to brighten an image based on its current brightness.
        
        Args:
            brightness: Float from 0.0 (dark) to 1.0 (bright)
            max_enhancement: Maximum brightening factor to apply (default 2.0)
        
        Returns:
            Float representing the enhancement multiplier (1.0 = no change)
        """
        return 1.0 + (1.0 - brightness) ** 3.9 * (max_enhancement - 1.0)

    bot = SlashCommandGroup("escpos", "Various little commands of dubious utility")

    @bot.command(name="print", description="Print a message on the printer (5 second cooldown)")
    @commands.cooldown(1, 5, commands.BucketType.user) 
    @option("texttoprint", description="The text you want to print (200 character limit)", required=True)
    async def print_message(self, ctx, texttoprint: str):
        await ctx.defer()
        if not await self.verify_configuration_valid(ctx): return

        print(self.allowed_role_ids)

        member = ctx.guild.get_member(ctx.author.id)
        if not member or not any(role_id in [role.id for role in member.roles] for role_id in self.allowed_role_ids):
            print(f"[escpos ] [print] User '{ctx.author.id}' does not have the required roles to use the print command")
            await ctx.respond("You don't have the required role to use this command")
            raise commands.CheckFailure
        callerDisplayname = member.display_name
        callerUsername = member.name

        msg = await ctx.respond(f"Preparing to print your text")
        print(f"[escpos ] [print] User '{callerDisplayname} ({callerUsername})' is printing message: {texttoprint}")
        try:
            if len(texttoprint) > 200:
                raise ValueError("The text to print is too long. Please limit it to 200 characters")
            
            if self.verbosity_to_discord: await msg.edit("Connecting to the printer... (1/2)")
            printer = Network(self.printer_ip, self.printer_port, profile=self.printer_profile)
            printer.open()
            if printer.paper_status() == 0:
                printer.close()
                raise Exception("There is no paper in the printer")
            print("[escpos ] [print] Opened printer")
            if self.verbosity_to_discord: await msg.edit("Connected, now printing your text... (2/2)")
            printer.text(f"Message from '{callerDisplayname} ({callerUsername})':\n{texttoprint}\n")
            printer.cut()
            printer.close()
            print("[escpos ] [print] Closed printer")
        except Exception as e:
            print(repr(e))
            await msg.edit(f"An error occurred while trying to print: {repr(e)}")
            return
        await msg.edit(f"Message '{texttoprint}' printed successfully")

    @bot.command(name="image", description="Print an image on the printer (15 second cooldown)")
    @commands.cooldown(1, 15, commands.BucketType.user) 
    @option("imagetoprint", type=discord.Attachment, description="The image you want to print", required=True)
    @option("multitone", type=bool, description="Higher quality by using 8 shades of gray instead of 2", required=False)
    async def print_image(self, ctx: discord.ApplicationContext, imagetoprint: discord.Attachment, multitone: bool = False):
        await ctx.defer()
        if not await self.verify_configuration_valid(ctx): return
        
        member = ctx.guild.get_member(ctx.author.id)
        if not member or not any(role_id in [role.id for role in member.roles] for role_id in self.allowed_role_ids):
            print(f"[escpos ] [image] User '{ctx.author.id}' does not have the required roles to use the print command")
            await ctx.respond("You don't have the required role to use this command")
            raise commands.CheckFailure
        callerDisplayname = member.display_name
        callerUsername = member.name
        imagename = imagetoprint.filename

        msg = await ctx.respond(f"Preparing to print your image {imagename}")
        print(f"[escpos ] [image] User '{callerDisplayname} ({callerUsername})' is printing an image {imagename}")

        try:
            if not imagename.lower().endswith(self.supported_pil_image_types):
                raise ValueError(f"The file {imagename} is not an image. Supported types are: {(', '.join(self.supported_pil_image_types))}")
            print(f"[escpos ] [image] File is of type {(', '.join(self.supported_pil_image_types))}")
            
            if self.verbosity_to_discord: await msg.edit("Downloading your image (1/4)")
            print("[escpos ] [image] Downloading image")
            remote_file = requests.get(imagetoprint.url)

            image = Image.open(BytesIO(remote_file.content))
            print("[escpos ] [image] Image opened")
            # open image from file

            if self.verbosity_to_discord: await msg.edit("Applying processing to your image (2/4)")
            if not image.width < image.height:
                print("[escpos ] [image] Image is wide, rotating to landscape")
                image = image.rotate(270, expand=True)
            image = image.convert("L")
            #Acquire image, rotate and grayscale it

            brightness = self.calculate_brightness(image)
            print(f"[escpos ] [image] Calculated brightness: {brightness}")
            brightness_enhancement = self.calculate_brightness_enhancement(brightness)
            print(f"[escpos ] [image] Calculated brightness enhancement: {brightness_enhancement}")
            brightnessfilter = ImageEnhance.Brightness(image)
            image = brightnessfilter.enhance(brightness_enhancement)
            # Calculate brightness to apply and apply it
        
            contrastfilter = ImageEnhance.Contrast(image)
            image = contrastfilter.enhance(0.8)
            #screenshot = screenshot.quantize(colors=8)
            # Reduce contrast a bit

            image.thumbnail((512, 768), Image.Resampling.NEAREST)
            # Resize to be max 512 wide and 768 tall
            print("[escpos ] [image] Adjusted, grayscaled and resized image")

            byteImage = BytesIO()
            image.save(byteImage, "JPEG")
            byteImage.seek(0)
            discordFile = discord.File(fp=byteImage, filename=imagename, description="Image uploaded for printing")
            print("[escpos ] [image] Created discord file object from processed image")

            if multitone:
                if not self.enable_multitone:
                    raise Exception("Multitoning is disabled in the configuration")
                print("[escpos ] [image] Processing multitone")
                contrastfilter = ImageEnhance.Contrast(image)
                image = contrastfilter.enhance(0.7)
                brightnessfilter = ImageEnhance.Brightness(image)
                image = brightnessfilter.enhance(1.28)

                tempBytes = BytesIO()
                tempBytes = multitoneImage(image=image, output_file=None, output_image=None, num_lines=100, resize=None, sharpness=None, contrast=None, cut=None, speed=1, heads_energizing=1, loglevel="INFO")
            
            if self.verbosity_to_discord: await msg.edit("Connecting to the printer... (3/4)")
            printer = Network(self.printer_ip, profile=self.printer_profile)
            printer.open()
            if printer.paper_status() == 0:
                printer.close()
                raise Exception("There is no paper in the printer")
            print("[escpos ] [image] Opened printer")
            try:
                if self.verbosity_to_discord: await msg.edit("Connected, now printing your image... (4/4)")
                printer.text(f"Image from '{callerDisplayname} ({callerUsername})':\n")
                if multitone:
                    print("[escpos ] [image] Printing multitone")
                    printer._raw(tempBytes)
                    printer.set_with_default()
                else:
                    print("[escpos ] [image] Printing normal")
                    printer.image(image, center=True, impl='graphics')
                
                printer.cut()
                printer.close()
                print("[escpos ] [image] Closed printer")
            except Exception as e:
                printer.close()
                raise e
        except Exception as e:
            print(repr(e))
            await msg.edit(f"An error occurred while trying to print your image: {repr(e)}")
            #await ctx.respond(f"An error occurred while trying to print image: {repr(e)}")
            return
        await msg.edit(f"Image {imagename} printed successfully", file=discordFile)

    @bot.command(name="supportedimagetypes", description="Check what types of images are supported")
    async def supported_image_types(self, ctx):
        await ctx.defer()
        member = ctx.guild.get_member(ctx.author.id)
        callerDisplayname = member.display_name
        callerUsername = member.name
        try:
            await ctx.respond(f"Hi {callerDisplayname}, image types supported right now are {(', '.join(self.supported_pil_image_types))}")
        except Exception as e:
            print(repr(e))
            await ctx.respond(f"An error occurred while: {repr(e)}")
            return

    @bot.command(name="paperstatus", description="Check how much paper is left in the printer")
    @commands.cooldown(1, 10, commands.BucketType.user) 
    async def paper_status(self, ctx: discord.ApplicationContext):
        await ctx.defer()
        msg = await ctx.respond("Checking the paper status")
        try:
            if self.verbosity_to_discord: await msg.edit("Connecting to the printer... (1/1)")
            printer = Network(self.printer_ip, self.printer_port, profile=self.printer_profile)
            printer.open()
            print("[escpos ] [paper_status] Opened printer")
            paper_status = self.parse_paper_status(printer.paper_status())
            printer.close()
        except Exception as e:
            print(repr(e))
            await msg.edit(f"An error occurred while getting paper status: {repr(e)}")
            return
        await msg.edit(f"Paper Status: {paper_status}")

    @bot.command(name="chat", description="Send a message to chat")
    @option("texttoprint", description="The text you want to send (500 character limit)", required=True)
    async def chat_message(self, ctx: discord.ApplicationContext, texttoprint: str):
        await ctx.defer()
        member = ctx.guild.get_member(ctx.author.id)
        callerDisplayname = member.display_name
        callerUsername = member.name
        try:
            if len(texttoprint) > 500:
                raise ValueError("The text to print is too long. Please limit it to 500 characters")
            await ctx.respond(f"{callerDisplayname}: '{texttoprint}'")
        except Exception as e:
            print(repr(e))
            await ctx.respond(f"An error occurred while: {repr(e)}")
            return

def setup(bot): # this is called by Pycord to setup the cog
    bot.add_cog(escpos(bot)) # add the cog to the bot