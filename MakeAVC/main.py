import discord
from dotenv import load_dotenv
import os
# Load env variables for bot and channel
load_dotenv()
bot_token = os.getenv("BOT_TOKEN")
#print(bot_token)
vc_id = os.getenv("CHANNEL_ID")
#print(vc_id)

intents = discord.Intents.default()
intents.members = True
intents.voice_states = True
intents.presences = True

bot = discord.Client(intents=intents)

TARGET_VOICE_CHANNEL_ID = int(vc_id)

# Dictionary to store created channels for each user
created_channels = {}

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}!')

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
                # ... add other permissions as needed
            )
        }

        new_channel = await after.channel.guild.create_voice_channel(
            name=f"{channel_name}'s VC{game_name}",  # Include game_name if available
            category=after.channel.category,
            overwrites=overwrites
        )
        await member.move_to(new_channel)
        created_channels[member.id] = new_channel
        print(f"Created channel for {member.name}: {new_channel.name}")

    elif before.channel: # User left a voice channel
        if len(before.channel.members) == 0 and before.channel.id in [channel.id for channel in created_channels.values()]:
            print(f"Deleting channel: {before.channel.name}")
            # Find the ID of the user who created this channel
            creator_id = next((user_id for user_id, channel in created_channels.items() if channel.id == before.channel.id),
                              None)
            await before.channel.delete()
            if creator_id:  # Only delete from the dictionary if we found the creator
                del created_channels[creator_id]


bot.run(bot_token)