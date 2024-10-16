import asyncio
import discord
import pathlib
import os
import random
import re
import json
import pandas as pd
from datetime import datetime
from collections import deque
from dotenv import load_dotenv
from shared import reaction_role_mapping, save_role_data, load_role_data
from pointscommand import handle_points_command
from autoupdater import run_update_clan
from rsn import handle_rsn_command
from otwselect import handle_otwselect_command
from updateclan import run_clan_update
from importjson import handle_importjson_command
from csvexport import handle_export_command
from jpadd import handle_jpadd_command
from customcommands import handle_add_command, handle_remove_command, handle_edit_command, handle_list_commands, handle_custom_command, load_custom_commands
from reactrole import handle_reaction, handle_reactrole_command, assign_or_remove_roles_for_existing_reactions, save_role_data, load_role_data, on_raw_reaction_add, on_raw_reaction_remove
from memberlist import handle_memberlist_command
from makeavc import load_channels_from_json, save_channels_to_json, check_and_delete_empty_channels, handle_voice_state_update

# Initialize the bot
intents = discord.Intents.default()
intents.members = True
intents.voice_states = True
intents.presences = True
intents.message_content = True
intents.reactions = True
intents.guilds = True

bot = discord.Client(intents=intents)

# Load env variables for bot and channel
load_dotenv()
bot_token = os.getenv("BOT_TOKEN")
vc_id = os.getenv("CHANNEL_ID")
newbie_role_id = os.getenv("NEWBIE_ROLE_ID")
welcome_channel = os.getenv("WELCOME_MESSAGE_CHANNEL")
welcome_message = os.getenv("WELCOME_MESSAGE_ID")
admin_role_id = int(os.getenv("ADMIN_ROLE_ID"))
ANNOUNCEMENT_CHANNEL_ID = int(os.getenv("RANK_CHANNEL_ID"))

COMMANDS_FILE = pathlib.Path("data") / "custom_commands.json"

custom_commands = {}

async def run_periodically():
    default_channel = bot.get_channel(int(os.getenv("LOG_CHANNEL_ID")))
    while True:
        await run_update_clan(bot, default_channel=default_channel)
        await asyncio.sleep(6 * 60 * 60)  # Sleep for 6 hours

@bot.event
async def on_ready():
    print(f'Bot is ready. Logged in as {bot.user}')
    load_channels_from_json()
    await assign_or_remove_roles_for_existing_reactions(bot, reaction_role_mapping)
    await check_and_delete_empty_channels(bot)
    channel = bot.get_channel(int(welcome_channel))
    if channel:
        specific_message_id = int(welcome_message)
        async for message in channel.history(limit=None):
            if message.id == specific_message_id:
                continue
            else:
                try:
                    await message.delete()
                except discord.Forbidden:
                    print(f"Missing permissions to delete message with ID {message.id}")
                except Exception as e:
                    print(f"An error occurred while deleting message with ID {message.id}: {e}")

    bot.loop.create_task(run_periodically())

@bot.event
async def on_member_join(member):
    role = member.guild.get_role(int(newbie_role_id))
    if role:
        await member.add_roles(role)
        print(f"{member} has been given the joiner role.")
    else:
        print(f"Role with ID {newbie_role_id} not found.")

@bot.event
async def on_message(message):
    guild = message.guild
    content_lower = message.content.lower()

    if message.channel.id == int(welcome_channel) and message.id != int(welcome_message):
        await asyncio.sleep(5)
        await message.delete()

    if content_lower.startswith('!rsn ') and not message.author.bot:
        await handle_rsn_command(message, bot, guild, ANNOUNCEMENT_CHANNEL_ID)
        log_channel = bot.get_channel(int(os.getenv("LOG_CHANNEL_ID")))
        if log_channel:
            await log_channel.send(f"User {message.author} issued command: {message.content}")

    if content_lower.startswith('!points ') and not message.author.bot:
        await handle_points_command(message)

    if content_lower.startswith("!otwselect") and not message.author.bot:
        await handle_otwselect_command(message, admin_role_id, skill_of_the_week, boss_of_the_week)

    if message.content.startswith("!importjson") and not message.author.bot:
        await handle_importjson_command(message, admin_role_id)

    if message.content.startswith("!updateclan") and not message.author.bot:
        await run_clan_update(message, admin_role_id)

    if content_lower.startswith('!export') and not message.author.bot:
        await handle_export_command(message, admin_role_id)

    if content_lower.startswith('!jpadd') and not message.author.bot:
        await handle_jpadd_command(message, admin_role_id)

    if message.content.startswith('!reactrole') and message.author != bot.user:
        await handle_reactrole_command(message, admin_role_id, reaction_role_mapping, save_role_data)

    if content_lower.startswith('!addcommand') and not message.author.bot:
        await handle_add_command(message, admin_role_id)

    elif content_lower.startswith('!removecommand') and not message.author.bot:
        await handle_remove_command(message, admin_role_id)

    elif content_lower.startswith('!editcommand') and not message.author.bot:
        await handle_edit_command(message, admin_role_id)

    elif content_lower.startswith('!customcommands') and not message.author.bot:
        await handle_list_commands(message, admin_role_id)

    else:
        await handle_custom_command(message)

    if content_lower.startswith('!memberlist') and not message.author.bot:
        await handle_memberlist_command(message)

    if content_lower.startswith('!adminhelp') and not message.author.bot:
        commands = {
            "!rsn <rsn>": "Link your Discord ID to your RuneScape name.",
            "!points <rsn>": "Check the points of a RuneScape name.",
            "ADMIN: !otwselect": "Select the Boss of the Week and Skill of the Week.",
            "ADMIN: !importjson <json_data>": "Import clan member data from JSON.",
            "ADMIN: !updateclan": "Update the clan member data csv.",
            "ADMIN: !export": "Export the clan member data CSV to the chat.",
            "ADMIN: !jpadd <rsn>": "Add Joker Points to a RuneScape name.",
            "ADMIN: !reactrole <message_id> <emoji> <@role_to_add> [<@role_to_remove>] [--remove-reaction]": "Manage reaction roles.",
            "ADMIN: !reactrole <message_id> <emoji> --remove": "Remove a reaction role.",
            "ADMIN: !reactrole <message_id> --remove-message": "Remove all reaction roles from a message.",
            "ADMIN: !addcommand <command_name> <response>": "Add a custom command.",
            "ADMIN: !editcommand <command_name> <new_response>": "Edit a custom command.",
            "ADMIN: !removecommand <command_name>": "Remove a custom command."
        }

        embed = discord.Embed(title="Bot Commands", color=discord.Color.blue())
        for command, description in commands.items():
            embed.add_field(name=command, value=description, inline=False)

        await message.channel.send(embed=embed)

@bot.event
async def on_raw_reaction_add(payload):
    await handle_reaction(bot, payload, 'add')

@bot.event
async def on_raw_reaction_remove(payload):
    await handle_reaction(bot, payload, 'remove')

@bot.event
async def on_voice_state_update(member, before, after):
    await handle_voice_state_update(bot, member, before, after)

bot.run(bot_token)