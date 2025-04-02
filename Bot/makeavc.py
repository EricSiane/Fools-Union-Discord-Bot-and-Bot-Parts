import os
import json
import discord
import pathlib
from dotenv import load_dotenv

load_dotenv()
DATA_DIR = pathlib.Path("data")
TARGET_VOICE_CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

created_channels = {}
json_file_path = DATA_DIR / "created_channels.json"

def load_channels_from_json():
    global created_channels
    if os.path.exists(json_file_path):
        try:
            with open(json_file_path, "r") as f:
                created_channels = json.load(f)
                print(f"Loaded created channels: {created_channels}")
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
        except Exception as e:
            print(f"Error loading JSON file: {e}")
    else:
        print(f"JSON file does not exist: {json_file_path}")

def save_channels_to_json():
    try:
        with open(json_file_path, "w") as f:
            json.dump(created_channels, f)
            print(f"Saved created channels: {created_channels}")
    except Exception as e:
        print(f"Error saving JSON file: {e}")

async def check_and_delete_empty_channels(bot):
    for guild in bot.guilds:
        for user_id, channel_id in list(created_channels.items()):
            channel = guild.get_channel(channel_id)
            if channel:
                print(f"Checking channel: {channel.name} (ID: {channel.id}) with {len(channel.members)} members")
                if len(channel.members) == 0:
                    try:
                        await channel.delete()
                        print(f"Deleted empty channel: {channel.name} (ID: {channel.id})")
                        del created_channels[user_id]
                    except discord.Forbidden:
                        print(f"Bot doesn't have permission to delete channel: {channel.name}")
                    except discord.HTTPException as e:
                        print(f"Failed to delete channel {channel.name} due to an error: {e}")
            else:
                print(f"Channel with ID {channel_id} not found")
    save_channels_to_json()

async def handle_voice_state_update(bot, member, before, after):
    if after.channel and after.channel.id == TARGET_VOICE_CHANNEL_ID:
        if member.id in created_channels:
            existing_channel_id = created_channels[member.id]
            existing_channel = member.guild.get_channel(existing_channel_id)
            if existing_channel:
                await member.move_to(existing_channel)
                print(f"Moved {member.name} to their existing channel: {existing_channel.name}")
                return

        channel_name = member.nick if member.nick else member.name
        game_name = f" - {member.activity.name}" if member.activity and member.activity.type == discord.ActivityType.playing else ""

        overwrites = {
            member: discord.PermissionOverwrite(
                manage_channels=True,
                manage_permissions=True,
                view_channel=True,
                connect=True,
                speak=True,
                mute_members=False,
                deafen_members=False,
                move_members=True,
            )
        }

        new_channel = await after.channel.guild.create_voice_channel(
            name=f"{channel_name}'s VC{game_name}",
            category=after.channel.category,
            overwrites=overwrites
        )
        await member.move_to(new_channel)
        created_channels[member.id] = new_channel.id
        save_channels_to_json()
        print(f"Created channel for {member.name}: {new_channel.name}")

    elif before.channel and len(before.channel.members) == 0 and before.channel.id in created_channels.values():
        print(f"Deleting channel: {before.channel.name}")
        creator_id = next((user_id for user_id, channel_id in created_channels.items() if channel_id == before.channel.id), None)
        await before.channel.delete()
        if creator_id:
            del created_channels[creator_id]
            save_channels_to_json()