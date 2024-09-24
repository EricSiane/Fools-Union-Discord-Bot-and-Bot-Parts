import discord
from discord.ext import commands
import json
import os

# Set up the bot
intents = discord.Intents.default()
intents.reactions = True  # Enable reaction-related events
intents.guilds = True
intents.members = True  # Required for managing roles
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# File to save message and role data
DATA_FILE = 'reaction_roles.json'


# Load data from the JSON file
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {}


# Save data to the JSON file
def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)


# Load initial data
reaction_role_mapping = load_data()


# Command to add a reaction and role mapping to a message
@bot.command()
async def react(ctx, message_id: int, emoji: str, role: discord.Role):
    try:
        message = await ctx.channel.fetch_message(message_id)
        await message.add_reaction(emoji)

        # Save the reaction and role mapping to the JSON file
        reaction_role_mapping[str(message_id)] = {
            "emoji": emoji,
            "role_id": role.id
        }
        save_data(reaction_role_mapping)

        await ctx.send(f"Added {emoji} reaction to the message with ID: {message_id} and assigned role {role.name}")
    except discord.NotFound:
        await ctx.send("Message not found!")
    except discord.HTTPException as e:
        await ctx.send(f"Failed to react to the message. Error: {e}")


# Event listener for when a user adds a reaction
@bot.event
async def on_raw_reaction_add(payload):
    message_id = str(payload.message_id)

    if message_id in reaction_role_mapping:
        data = reaction_role_mapping[message_id]

        # Check if the reaction matches the one stored
        if str(payload.emoji) == data['emoji']:
            guild = bot.get_guild(payload.guild_id)
            role = guild.get_role(data['role_id'])
            member = guild.get_member(payload.user_id)

            if role and member and not member.bot:
                await member.add_roles(role)


# Event listener for when a user removes a reaction
@bot.event
async def on_raw_reaction_remove(payload):
    message_id = str(payload.message_id)

    if message_id in reaction_role_mapping:
        data = reaction_role_mapping[message_id]

        # Check if the reaction matches the one stored
        if str(payload.emoji) == data['emoji']:
            guild = bot.get_guild(payload.guild_id)
            role = guild.get_role(data['role_id'])
            member = guild.get_member(payload.user_id)

            if role and member and not member.bot:
                await member.remove_roles(role)

bot.run("TOKEN")