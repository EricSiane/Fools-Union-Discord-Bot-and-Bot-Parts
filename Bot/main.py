import json
import pandas as pd
import argparse
import discord
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os
import random
from collections import deque
import json

csv_file = "fools_union_member_data.csv"

df = pd.read_csv(csv_file)

# Lists needed for BOTW & SOTW
skill_of_the_week = ["Runecraft", "Construction", "Agility", "Herblore", "Thieving", "Crafting", "Fletching", "Slayer", "Hunter", "Mining", "Smithing", "Fishing", "Cooking", "Firemaking", "Woodcutting", "Farming"]


boss_of_the_week = ["Abyssal Sire", "Alchemical Hydra", "Araxxor", "Barrows", "Bryophyta", "Callisto", "Vet'ion", "Cerberus", "Chaos Elemental", "Chaos Fanatic", "Commander Zilyana", "Corporeal Beast", "Crazy Archaeologist", "Dagannoth Prime", "Dagannoth Rex", "Dagannoth Supreme",
 "Deranged Archaeologist", "Duke Sucellus", "General Graardor", "Giant Mole", "Grotesque Guardians",
 "Kalphite Queen", "King Black Dragon", "Kraken", "Kree'Arra", "K'ril Tsutsaroth", "Nex", "Nightmare", "Obor", "Phantom Muspah", "Sarachnis", "Scorpia", "Scurrius", "Skotizo", "Tempoross", "The Gauntlet", "The Leviathan", "The Whisperer", "Thermonuclear Smoke Devil", "TzTok-Jad", "Vardorvis", "Venenatis", "Vorkath", "Wintertodt", "Zalcano", "Zulrah"]


#Bot Init Start
intents = discord.Intents.default()
intents.members = True
intents.voice_states = True
intents.presences = True
intents.message_content = True

bot = discord.Client(intents=intents)
# Load env variables for bot and channel
load_dotenv()
bot_token = os.getenv("BOT_TOKEN")
#print(bot_token)
vc_id = os.getenv("CHANNEL_ID")
#print(vc_id)
#Bot Init End

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}!')

@bot.event
async def on_message(message):
    guild = message.guild
    content_lower = message.content.lower()

    if content_lower.startswith('!rsn') and not message.author.bot:
        rsn = content_lower[len('!rsn '):].strip()

        df['rsn_lower'] = df['rsn'].str.lower()
        fools = discord.utils.get(guild.roles, name="Fools")
        iron = discord.utils.get(guild.roles, name="Iron Bar")
        guest = discord.utils.get(guild.roles, name="Guest")

        if rsn in df['rsn_lower'].values:

            index = df.index[df['rsn_lower'] == rsn].tolist()[0]

            df.at[index, 'Discord'] = str(message.author.id)

            df.to_csv(csv_file, index=False)

            await message.channel.send(f"Discord ID {message.author.mention} has been linked to RSN '{df.at[index, 'rsn']}'.")
            await message.author.add_roles(fools)
            await message.author.add_roles(iron)
            await message.author.remove_roles(guest)
        else:
            await message.channel.send(f"RSN '{rsn}' not found in the clan list. if you aren't in the clan, welcome as a guest!")
            await message.author.add_roles(guest)
#Start OTW Selection
    if content_lower.startswith("!otwselect") and not message.author.bot:
        # Choose boss, ensuring it's not in the last 3
        # Load data if it exists for BOTW & SOTW
        data_file_path = 'selection_data.json'

        if os.path.exists(data_file_path):
            with open(data_file_path, 'r') as f:
                data = json.load(f)
                last_3_bosses = deque(data['last_3_bosses'], maxlen=3)
                last_3_skills = deque(data['last_3_skills'], maxlen=3)
            # Debug notifications
            print("DEBUG: Loaded previous selections:")
            print("Last 3 bosses:", list(last_3_bosses))
            print("Last 3 skills:", list(last_3_skills))
        else:
            last_3_bosses = deque(maxlen=3)
            last_3_skills = deque(maxlen=3)
        while True:
            boss_choice = random.choice(boss_of_the_week)
            if boss_choice not in last_3_bosses:
                break
        last_3_bosses.append(boss_choice)

        # Choose skill, ensuring it's not in the last 3
        while True:
            skill_choice = random.choice(skill_of_the_week)
            if skill_choice not in last_3_skills:
                break
        last_3_skills.append(skill_choice)

        await message.channel.send(f"Boss of the Week: {boss_choice}\nSkill of the Week: {skill_choice}")

        # Save updated data
        with open(data_file_path, 'w') as f:
            data = {
                'last_3_bosses': list(last_3_bosses),
                'last_3_skills': list(last_3_skills)
            }
            json.dump(data, f)

        # Debug notifications (optional)
        print("DEBUG: Updated lists after selection:")
        print("Last 3 bosses:", list(last_3_bosses))
        print("Last 3 skills:", list(last_3_skills))
#End OTW Selection
    if content_lower.startswith('!export') and not message.author.bot:
        try:
            file = discord.File("fools_union_member_data.csv")
            await message.channel.send("Here is the file you requested:", file=file)
        except Exception as e:
            await message.channel.send(f"Failed to send file: {e}")

    if content_lower.startswith('!jpadd') and not message.author.bot:
        try:
            # Parse the command and extract the RSN name
            rsn = content_lower[len('!jpadd '):].strip()

            # Convert RSN in DataFrame to lowercase for comparison
            df['rsn_lower'] = df['rsn'].str.lower()

            if rsn in df['rsn_lower'].values:
                index = df.index[df['rsn_lower'] == rsn].tolist()[0]

                # Add 10 points to "Other Points"
                df.at[index, 'Other Points'] += 5

                # Save the DataFrame back to the CSV
                df.to_csv(csv_file, index=False)

                await message.channel.send(
                    f"Added 10 points to '{df.at[index, 'rsn']}'. New total: {df.at[index, 'Other Points']} points.")
            else:
                await message.channel.send(f"RSN '{rsn}' not found in the clan list.")
        except Exception as e:
            await message.channel.send(f"An error occurred: {str(e)}")

#Start MakeAVC
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

#End MakeAVC

bot.run(bot_token)