import asyncio
import discord
import pathlib
import os
import pytz
from datetime import datetime, timedelta
from dotenv import load_dotenv

from jpremove import handle_jpremove_command
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
from rankupdater import update_member_ranks, handle_rank_update_command

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

skill_of_the_week = ["Runecraft", "Construction", "Agility", "Herblore", "Thieving", "Crafting", "Fletching", "Slayer", "Hunter", "Mining", "Smithing", "Fishing", "Cooking", "Firemaking", "Woodcutting", "Farming"]

boss_of_the_week = ["Abyssal Sire", "Alchemical Hydra" ,"Amoxliatl", "Araxxor", "Barrows", "Bryophyta", "Callisto", "Vet'ion", "Cerberus", "Chaos Elemental", "Chaos Fanatic", "Commander Zilyana", "Corporeal Beast", "Crazy Archaeologist", "Dagannoth Prime", "Dagannoth Rex", "Dagannoth Supreme",
 "Deranged Archaeologist", "Duke Sucellus", "General Graardor", "Giant Mole", "Grotesque Guardians",
 "Kalphite Queen", "King Black Dragon", "Kraken", "Kree'Arra", "K'ril Tsutsaroth", "Nex", "Nightmare", "Obor", "Phantom Muspah", "Sarachnis", "Scorpia", "Scurrius", "Skotizo", "The Gauntlet", "The Leviathan", "The Hueycoatl", "The Whisperer", "Thermonuclear Smoke Devil", "TzTok-Jad", "Vardorvis", "Venenatis", "Vorkath", "Zalcano", "Zulrah"]

custom_commands = {}
load_custom_commands()
async def run_periodically():
    default_channel = bot.get_channel(int(os.getenv("LOG_CHANNEL_ID")))
    if not default_channel:
        print("Log channel not found.")
        return

    utc = pytz.utc
    now = datetime.now(utc)
    target_time = now.replace(hour=0, minute=0, second=0, microsecond=0)

    if now > target_time:
        target_time += timedelta(days=1)

    initial_delay = (target_time - now).total_seconds()
    await asyncio.sleep(initial_delay)

    while True:
        await run_update_clan(bot, default_channel=default_channel)
        # Also run the rank updater once per day
        for guild in bot.guilds:
            await update_member_ranks(bot, guild.id)
        await asyncio.sleep(24 * 60 * 60)



@bot.event
async def on_ready():
    print(f'Bot is ready. Logged in as {bot.user}')
    load_channels_from_json()
    await assign_or_remove_roles_for_existing_reactions(bot, reaction_role_mapping)
    await check_and_delete_empty_channels(bot)


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
    default_channel = bot.get_channel(int(os.getenv("LOG_CHANNEL_ID")))
    guild = message.guild
    content_lower = message.content.lower()

    if message.channel.id == int(welcome_channel):
        if not message.author.guild_permissions.administrator:
            await message.delete(delay=5)


    if content_lower.startswith('!rsn ') and not message.author.bot:
        await handle_rsn_command(message, bot, guild, ANNOUNCEMENT_CHANNEL_ID)
        log_channel = bot.get_channel(int(os.getenv("LOG_CHANNEL_ID")))
        if log_channel:
            await log_channel.send(f"User {message.author} issued command: {message.content}")
        await run_update_clan(bot, default_channel=default_channel)

    if content_lower.startswith('!points ') and not message.author.bot:
        await handle_points_command(message)
        await run_update_clan(bot, default_channel=default_channel)

    if content_lower.startswith("!otwselect") and not message.author.bot:
        await handle_otwselect_command(message, admin_role_id, skill_of_the_week, boss_of_the_week)
        await run_update_clan(bot, default_channel=default_channel)

    if message.content.startswith("!importjson") and not message.author.bot:
        await handle_importjson_command(message, admin_role_id)
        await run_update_clan(bot, default_channel=default_channel)

    if message.content.startswith("!updateclan") and not message.author.bot:
        await run_clan_update(message, admin_role_id)

    if content_lower.startswith('!export') and not message.author.bot:
        await handle_export_command(message, admin_role_id)
        await run_update_clan(bot, default_channel=default_channel)

    if content_lower.startswith('!jpadd') and not message.author.bot:
        await handle_jpadd_command(message, admin_role_id)
        await run_update_clan(bot, default_channel=default_channel)

    if content_lower.startswith('!jpremove') and not message.author.bot:
        await handle_jpremove_command(message, admin_role_id)
        await run_update_clan(bot, default_channel=default_channel)

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
        await run_update_clan(bot, default_channel=default_channel)

    if content_lower.startswith('!rankupdate') and not message.author.bot:
        await handle_rank_update_command(message, admin_role_id)
        log_channel = bot.get_channel(int(os.getenv("LOG_CHANNEL_ID")))
        if log_channel:
            await log_channel.send(f"User {message.author} issued command: {message.content}")

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
            "ADMIN: !removecommand <command_name>": "Remove a custom command.",
            "ADMIN: !rankupdate": "Manually update Discord roles based on clan ranks in the CSV file."
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