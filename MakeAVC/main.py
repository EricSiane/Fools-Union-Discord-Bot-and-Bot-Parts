import discord
from dotenv import load_dotenv
import os
import json

# Load env variables for bot and channel
load_dotenv()
bot_token = os.getenv("BOT_TOKEN")
vc_id = os.getenv("CHANNEL_ID")

intents = discord.Intents.default()
intents.members = True
intents.voice_states = True
intents.presences = True

bot = discord.Client(intents=intents)

TARGET_VOICE_CHANNEL_ID = int(vc_id)

# Dictionary to store created channels for each user
created_channels = {}

# Path to store JSON data
json_file_path = "created_channels.json"


# Function to load created channels from JSON
def load_channels_from_json():
    global created_channels
    if os.path.exists(json_file_path):
        with open(json_file_path, "r") as f:
            created_channels = json.load(f)


# Function to save created channels to JSON
def save_channels_to_json():
    with open(json_file_path, "w") as f:
        json.dump(created_channels, f)


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}!')

    # Load the created channels from the JSON file when the bot starts
    load_channels_from_json()

    # Check if the channels still exist and delete the ones that don't
    guild = discord.utils.get(bot.guilds, id=int(vc_id))
    if guild:
        for user_id, channel_id in list(created_channels.items()):
            channel = guild.get_channel(channel_id)
            if not channel:  # If the channel doesn't exist, remove it from the dictionary
                del created_channels[user_id]
        save_channels_to_json()


@bot.event
async def on_voice_state_update(member, before, after):
    if after.channel and after.channel.id == TARGET_VOICE_CHANNEL_ID:
        # User joined the target voice channel

        # Get the user's nickname or username
        channel_name = member.nick if member.nick else member.name

        # Check if the user is currently playing a game
        game_name = ""
        if member.activity and member.activity.type == discord.ActivityType.playing:
            game_name = f" - {member.activity.name}"

        # Create an overwrite for the member with full permissions
        overwrites = {
            member: discord.PermissionOverwrite(
                manage_channels=True,
                manage_permissions=True,
                view_channel=True,
                connect=True,
                speak=True,
                mute_members=True,
                deafen_members=True,
                move_members=True,
            )
        }

        new_channel = await after.channel.guild.create_voice_channel(
            name=f"{channel_name}'s VC{game_name}",  # Include game_name if available
            category=after.channel.category,
            overwrites=overwrites
        )
        await member.move_to(new_channel)
        created_channels[member.id] = new_channel.id  # Save the channel ID instead of the object
        save_channels_to_json()
        print(f"Created channel for {member.name}: {new_channel.name}")

    elif before.channel:  # User left a voice channel
        if len(before.channel.members) == 0 and before.channel.id in created_channels.values():
            print(f"Deleting channel: {before.channel.name}")
            # Find the ID of the user who created this channel
            creator_id = next(
                (user_id for user_id, channel_id in created_channels.items() if channel_id == before.channel.id), None)
            await before.channel.delete()
            if creator_id:  # Only delete from the dictionary if we found the creator
                del created_channels[creator_id]
                save_channels_to_json()


bot.run(bot_token)