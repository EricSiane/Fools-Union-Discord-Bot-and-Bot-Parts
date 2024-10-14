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


DATA_DIR = pathlib.Path("data")

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

COMMANDS_FILE = DATA_DIR / "custom_commands.json"

custom_commands = {}
reaction_role_mapping = {}
#Bot Init End

#Defs
def handle_storedata_command(data_to_import):
    try:
        # 1. Parse the imported data
        imported_data = json.loads(data_to_import)

        # Remove trailing spaces from values in the imported data
        for entry in imported_data:
            for key, value in entry.items():
                if isinstance(value, str):
                    entry[key] = value.rstrip()

        # 2. (Optional) Read existing data from your JSON file
        try:
            with open(DATA_DIR / 'clan_member_data.json', 'r') as f:
                existing_data = json.load(f)

            # Remove trailing spaces from values in the existing data
            for entry in existing_data:
                for key, value in entry.items():
                    if isinstance(value, str):
                        entry[key] = value.rstrip()

        except FileNotFoundError:
            existing_data = []  # Start with an empty list if the file doesn't exist
        existing_data.extend(imported_data)
        with open(DATA_DIR / 'clan_member_data.json', 'w') as f:
            # Ensure no trailing whitespace when writing
            json_str = json.dumps(existing_data, indent=4)
            f.write(json_str.rstrip() + "\n")  # Add newline for clarity

        return "Data imported successfully!"

    except json.JSONDecodeError:
        return "Error: Invalid JSON data provided."

# Data handling functions
def save_data(data):
    with open(DATA_DIR / 'reaction_role_mapping.json', 'w') as f:
        json.dump(data, f, indent=4)

def load_data():
    global reaction_role_mapping
    try:
        with open(DATA_DIR / 'reaction_role_mapping.json', 'r') as f:
            reaction_role_mapping = json.load(f)
    except FileNotFoundError:
        reaction_role_mapping = {}

def load_custom_commands():
    global custom_commands
    try:
        with open(DATA_DIR / 'custom_commands.json', 'r') as f:
            content = f.read().strip()
            if content:
                custom_commands = json.loads(content)
            else:
                custom_commands = {}
    except FileNotFoundError:
        custom_commands = {}

def save_custom_commands():
    with open(DATA_DIR / 'custom_commands.json', 'w') as f:
        json.dump(custom_commands, f, indent=4)
# Load data on startup
load_data()
load_custom_commands()

async def assign_or_remove_roles_for_existing_reactions():
    # Assign or remove roles for users who reacted or unreacted while the bot was offline.
    for message_id, mapping in reaction_role_mapping.items():
        guild = discord.utils.get(bot.guilds, id=mapping.get("guild_id"))
        channel = guild.get_channel(mapping.get("channel_id"))
        if not channel:
            continue
        try:
            message = await channel.fetch_message(int(message_id))

            # Iterate over the mappings for each emoji and role IDs
            for emoji, role_data in mapping['mappings'].items():
                role_to_add = guild.get_role(role_data["add"])  # Get the "add" role
                role_to_remove = guild.get_role(role_data["remove"])  # Get the "remove" role
                reacted_users = set()  # Store users who reacted with this emoji

                # Collect users who reacted with the expected emoji
                for reaction in message.reactions:
                    if str(reaction.emoji) == emoji:
                        async for user in reaction.users():
                            if user != bot.user:
                                member = guild.get_member(user.id) or await guild.fetch_member(user.id)
                                reacted_users.add(member.id)

                                # Manage roles based on reaction
                                if role_to_add not in member.roles:
                                    try:
                                        await member.add_roles(role_to_add)
                                        print(f"Assigned role {role_to_add.name} to {member.name}")
                                    except discord.Forbidden:
                                        print(f"Bot doesn't have permission to assign the role {role_to_add.name} to {member.name}")
                                    except discord.HTTPException as e:
                                        print(f"Failed to assign role {role_to_add.name} due to an error: {e}")

                                if role_to_remove in member.roles:
                                    try:
                                        await member.remove_roles(role_to_remove)
                                        print(f"Removed role {role_to_remove.name} from {member.name}")
                                    except discord.Forbidden:
                                        print(f"Bot doesn't have permission to remove the role {role_to_remove.name} from {member.name}")
                                    except discord.HTTPException as e:
                                        print(f"Failed to remove role {role_to_remove.name} due to an error: {e}")

                                # Remove the user's reaction
                                await message.remove_reaction(emoji, user)

                # Now check for users who have the "add" role but didn't react
                role_to_add_members = set(member.id for member in guild.members if role_to_add in member.roles)

                for member_id in (role_to_add_members - reacted_users):
                    member = guild.get_member(member_id) or await guild.fetch_member(member_id)
                    if member:
                        try:
                            if member_id in role_to_add_members and role_to_add.name != "Guest":  # Exclude "Guest" role from removal
                                await member.remove_roles(role_to_add)
                                print(f"Removed role {role_to_add.name} from {member.name}")
                            # We don't need to add the "remove" role back here
                        except discord.Forbidden:
                            print(f"Bot doesn't have permission to manage roles for {member.name}")
                        except discord.HTTPException as e:
                            print(f"Failed to manage roles due to an error: {e}")

        except discord.NotFound:
            print(f"Message with ID {message_id} not found")
        except discord.HTTPException as e:
            print(f"Error fetching message or assigning/removing roles: {e}")

#Start Bot commands
@bot.event
async def on_ready():
    print(f'Bot is ready. Logged in as {bot.user}')
    await assign_or_remove_roles_for_existing_reactions()
    await check_and_delete_empty_channels()
    channel = bot.get_channel(int(welcome_channel))
    if channel:
        specific_message_id = int(welcome_message)  # Assuming welcome_message contains the message ID

        async for message in channel.history(limit=None):
            if message.id == specific_message_id:  # Keep the specific message
                continue  # Skip to the next message
            else:
                try:
                    await message.delete()
                    # Optional: Add a small delay to avoid rate limits
                    # await asyncio.sleep(0.5)  # Adjust the delay as needed
                except discord.Forbidden:
                    print(f"Missing permissions to delete message with ID {message.id}")
                except Exception as e:
                    print(f"An error occurred while deleting message with ID {message.id}: {e}")
    @bot.event
    async def on_member_join(member):
        role = member.guild.get_role(int(newbie_role_id))

        if role:  # Check if the role exists
            await member.add_roles(role)
            print(f"{member} has been givin the joiner role.")
        else:
            print(f"Role with ID {newbie_role_id} not found.")

    @bot.event
    async def on_message(message):
        guild = message.guild
        content_lower = message.content.lower()

        if message.channel.id == int(welcome_channel) and message.id != int(welcome_message):
            await asyncio.sleep(5)
            await message.delete()

            # Checking for the '!rsn' command
        if content_lower.startswith('!rsn ') and not message.author.bot:
            rsn = content_lower[len('!rsn '):]

            csv_file = DATA_DIR / "fools_union_member_data.csv"
            df = pd.read_csv(csv_file, dtype={'Discord': str})
            rank_thresholds = [
                (0, "Bronze Bar"),
                (10, "Iron Bar"),
                (30, "Steel Bar"),
                (50, "Gold Bar"),
                (75, "Mithril Bar"),
                (100, "Adamant Bar"),
                (125, "Rune Bar"),
                (150, "Dragon Bar"),
                (200, "Onyx"),
                (250, "Zenyte")
            ]
            for threshold, rank in rank_thresholds:
                if total_points < threshold:
                    return rank
            return "Zenyte"

            df['Discord'] = df['Discord'].astype(str)
            df['rsn_lower'] = df['rsn'].str.lower()
            fools = discord.utils.get(guild.roles, name="Fools")
            iron = discord.utils.get(guild.roles, name="Iron Bar")
            guest = discord.utils.get(guild.roles, name="Guest")
            joiner = discord.utils.get(guild.roles, name="Joiner")

            if rsn in df['rsn_lower'].values:
                index = df.index[df['rsn_lower'] == rsn].tolist()[0]
                df.at[index, 'Discord'] = int(message.author.id)

                # Add 10 points if Discord ID is found in the Discord column and points haven't been added yet
                if str(message.author.id) in df['Discord'].values and df.at[index, 'Total Points'] == df.at[
                    index, 'Points From Time in Clan'] + df.at[index, 'Other Points']:
                    df.at[index, 'Total Points'] += 10

                new_points = df.at[index, 'Total Points']

                # Check if the new points exceed any rank threshold
                new_rank = None
                for threshold, rank in sorted(rank_thresholds):
                    if new_points >= threshold:
                        new_rank = rank
                    else:
                        break

                # Update the rank column if a new rank is achieved
                if new_rank:
                    df.at[index, 'rank'] = new_rank
                    announcement_channel = bot.get_channel(ANNOUNCEMENT_CHANNEL_ID)
                    await announcement_channel.send(f"{df.at[index, 'rsn']} has been promoted to {new_rank}!")

                df.to_csv(csv_file, index=False)

                original_rsn = df.at[index, 'rsn']
                sent_message = await message.channel.send(
                    f"Discord ID {message.author.mention} has been linked to RSN '{df.at[index, 'rsn']}'."
                )
                await message.author.add_roles(fools, iron)
                await message.author.remove_roles(guest)
                await message.author.remove_roles(joiner)

                await asyncio.sleep(10)  # Wait for 10 seconds
                await sent_message.delete()
                await message.delete()

                try:
                    await message.author.edit(nick=original_rsn)
                except discord.Forbidden:
                    await message.channel.send("I don't have permission to change your nickname.")
            else:
                await message.channel.send(
                    f"RSN '{rsn}' not found in the clan list. If you aren't in the clan, welcome as a guest!")
                await message.author.add_roles(guest)
                await message.author.remove_roles(joiner)
                try:
                    await message.author.edit(nick=rsn)  # Change nickname to the entered RSN
                except discord.Forbidden:
                    await message.channel.send("I don't have permission to change your nickname.")
#!Points Command
        if content_lower.startswith('!points ') and not message.author.bot:
            rsn = content_lower[len('!points '):].strip().lower()

            csv_file = DATA_DIR / "fools_union_member_data.csv"
            df = pd.read_csv(csv_file, dtype={'Discord': str})

            df['rsn_lower'] = df['rsn'].str.lower()

            if rsn in df['rsn_lower'].values:
                index = df.index[df['rsn_lower'] == rsn].tolist()[0]
                discord_value = df.at[index, 'Discord']
                discord_linked = not pd.isna(discord_value) and discord_value != '' and discord_value != 0
                time_in_clan = df.at[index, 'Days in Clan']
                other_points = df.at[index, 'Other Points']
                total_points = df.at[index, 'Total Points']
                # Define rank thresholds
                rank_thresholds = [
                    (0, "Bronze Bar"),
                    (10, "Iron Bar"),
                    (30, "Steel Bar"),
                    (50, "Gold Bar"),
                    (75, "Mithril Bar"),
                    (100, "Adamant Bar"),
                    (125, "Rune Bar"),
                    (150, "Dragon Bar"),
                    (200, "Onyx"),
                    (250, "Zenyte")
                ]
                for threshold, rank in rank_thresholds:
                    if total_points < threshold:
                        return rank
                return "Zenyte"

                # Determine the next rank and points needed
                next_rank = None
                points_needed = None
                for threshold, rank in rank_thresholds:
                    if total_points < threshold:
                        next_rank = rank
                        points_needed = threshold - total_points
                        break

                await message.channel.send(
                    f"RSN: {df.at[index, 'rsn']}\n"
                    f"Discord Linked: {'Yes' if discord_linked else 'No'}\n"
                    f"Time in Clan: {time_in_clan} days\n"
                    f"Other Points: {other_points}\n"
                    f"Total Points: {total_points}\n"
                    f"Next Rank: {next_rank}\n"
                    f"Points Needed for Next Rank: {points_needed}"
                )
            else:
                await message.channel.send(f"RSN '{rsn}' not found in the clan list.")

        # Checking for the '!otwselect' command
        if content_lower.startswith("!otwselect") and not message.author.bot:
            # Check if the user has the admin role
            if any(role.id == admin_role_id for role in message.author.roles):
                data_file_path = DATA_DIR / 'selection_data.json'

                # Load data if it exists for BOTW & SOTW
                if os.path.exists(data_file_path):
                    with open(data_file_path, 'r') as f:
                        data = json.load(f)
                        last_3_bosses = deque(data['last_3_bosses'], maxlen=3)
                        last_3_skills = deque(data['last_3_skills'], maxlen=3)
                else:
                    last_3_bosses = deque(maxlen=3)
                    last_3_skills = deque(maxlen=3)

                while True:
                    boss_choice = random.choice(boss_of_the_week)
                    if boss_choice not in last_3_bosses:
                        break
                last_3_bosses.append(boss_choice)

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
            else:
                await message.channel.send("You do not have permission to use this command.")
        # End OTW Selection

        # Import Clan JSON Data Start
        if message.content.startswith("!importjson") and not message.author.bot:
            # Check if the user has the admin role
            if any(role.id == admin_role_id for role in message.author.roles):
                json_data = message.content[len("!importjson") + 1:].strip()

                try:
                    result = handle_storedata_command(json_data)  # Use your existing function
                    await message.channel.send(result)
                    await message.delete()
                except Exception as e:
                    await message.channel.send(f"An error occurred during import: {e}")
            else:
                await message.channel.send("You do not have permission to use this command.")
        # Import Clan JSON Data End

        # Clan Updater

        if message.content.startswith("!updateclan") and not message.author.bot:
            # Check if the user has the admin role
            if any(role.id == admin_role_id for role in message.author.roles):
                # Define the file paths directly here
                JSON_FILE = DATA_DIR / "clan_member_data.json"
                CSV_FILE = DATA_DIR / "fools_union_member_data.csv"

                def load_data(json_file):
                    """Loads member data from a JSON file."""
                    with open(json_file, 'r') as f:
                        data = json.load(f)
                    return data

                def calculate_member_stats(members):
                    """Calculates additional stats for each member."""
                    today = datetime.today()
                    for member in members:
                        joined_date = datetime.strptime(member["joinedDate"], "%d-%b-%Y")
                        days_elapsed = (today - joined_date).days
                        member["days in clan"] = days_elapsed
                        member["points from time in clan"] = (days_elapsed // 5)
                        member["joinedDate"] = joined_date.strftime("%#m/%#d/%Y")  # Format date
                    return members

                def update_clan_csv(clan_csv, members):
                    """Updates the clan CSV with member data."""
                    for member in members:
                        # Check if member exists in CSV
                        existing_member = clan_csv[clan_csv['rsn'].str.rstrip() == member['rsn'].rstrip()]

                        if not existing_member.empty:
                            # Update existing member
                            index = existing_member.index[0]
                            clan_csv.at[index, 'Points From Time in Clan'] = member["points from time in clan"]
                            clan_csv.at[index, 'Days in Clan'] = member["days in clan"]
                        else:
                            # Add new member
                            clan_csv.loc[len(clan_csv)] = [
                                member['rsn'],
                                member["joinedDate"],
                                "Bronze Bar",
                                "",
                                member["days in clan"],
                                member["points from time in clan"],
                                0,
                                member["points from time in clan"],
                                [],
                                [],
                            ]
                    return clan_csv

                async def update_ranks(clan_csv):
                    """Updates ranks based on total points and sends rank-up messages."""

                    def get_new_rank(total_points):
                        """Determines the new rank based on total points."""
                        rank_thresholds = [
                            (0, "Bronze Bar"),
                            (10, "Iron Bar"),
                            (30, "Steel Bar"),
                            (50, "Gold Bar"),
                            (75, "Mithril Bar"),
                            (100, "Adamant Bar"),
                            (125, "Rune Bar"),
                            (150, "Dragon Bar"),
                            (200, "Onyx"),
                            (250, "Zenyte")
                        ]
                        for threshold, rank in reversed(rank_thresholds):
                            if total_points >= threshold:
                                return rank
                        return "Bronze Bar"

                    # Calculate total points and update ranks efficiently using pandas apply
                    clan_csv['Total Points'] = clan_csv['Points From Time in Clan'] + clan_csv['Other Points']
                    clan_csv['new_rank'] = clan_csv['Total Points'].apply(get_new_rank)

                    # Identify and collect rank changes
                    rank_changes = []
                    rank_changed = clan_csv['rank'] != clan_csv['new_rank']
                    for _, row in clan_csv[rank_changed].iterrows():
                        rank_changes.append((row['rsn'], row['new_rank']))
                        print(f"{row['rsn']} rank has changed to: {row['new_rank']}")

                    # Update the 'rank' column
                    clan_csv['rank'] = clan_csv['new_rank']
                    clan_csv.drop(columns=['new_rank'], inplace=True)  # Remove temporary column

                    print("Updated!")
                    return clan_csv, rank_changes

                async def main():
                    # Load data directly from the files
                    members = load_data(JSON_FILE)
                    members = calculate_member_stats(members)
                    clan_csv = pd.read_csv(CSV_FILE, dtype={'Discord': str})
                    clan_csv['rsn'] = clan_csv['rsn'].astype(str)

                    # Update CSV and ranks
                    clan_csv = update_clan_csv(clan_csv, members)
                    clan_csv, rank_changes = await update_ranks(clan_csv)

                    # Ensure the 'Discord' column is treated as a string before saving
                    clan_csv['Discord'] = clan_csv['Discord'].astype(str)
                    clan_csv.to_csv(CSV_FILE, index=False)

                    # Send rank-up messages
                    if rank_changes:
                        rank_up_messages = "\n".join(
                            [f"{rsn} has been promoted to {new_rank}!" for rsn, new_rank in rank_changes])
                        await message.channel.send(f"Rank Up Notifications:\n{rank_up_messages}")

                await main()
                await message.channel.send(f"Clan has been updated!")
            else:
                await message.channel.send("You do not have permission to use this command.")
            # Clan Updater End

        # Export Clan CSV to Discord Start
        if content_lower.startswith('!export') and not message.author.bot:
            # Check if the user has the admin role
            if any(role.id == admin_role_id for role in message.author.roles):
                try:
                    file = discord.File(DATA_DIR / "fools_union_member_data.csv")
                    await message.channel.send("Here is the file you requested:", file=file)
                except Exception as e:
                    await message.channel.send(f"Failed to send file: {e}")
            else:
                await message.channel.send("You do not have permission to use this command.")
        # Export Clan CSV to Discord end

        # Add Joker Points Start
        if content_lower.startswith('!jpadd') and not message.author.bot:
            # Check if the user has the admin role
            if any(role.id == admin_role_id for role in message.author.roles):
                csv_file = DATA_DIR / "fools_union_member_data.csv"
                df = pd.read_csv(csv_file, dtype={'Discord': str})
                try:
                    # Parse the command and extract the RSN name
                    rsn = content_lower[len('!jpadd '):].strip()

                    # Convert RSN in DataFrame to lowercase for comparison
                    df['rsn_lower'] = df['rsn'].str.lower()

                    if rsn in df['rsn_lower'].values:
                        index = df.index[df['rsn_lower'] == rsn].tolist()[0]

                        # Add 5 points to "Other Points"
                        df.at[index, 'Other Points'] += 5

                        # Calculate total points (Points From Time in Clan + Other Points)
                        df.at[index, 'Total Points'] = df.at[index, 'Points From Time in Clan'] + df.at[
                            index, 'Other Points']

                        # Define rank thresholds
                        rank_thresholds = [
                            (0, "Bronze Bar"),
                            (10, "Iron Bar"),
                            (30, "Steel Bar"),
                            (50, "Gold Bar"),
                            (75, "Mithril Bar"),
                            (100, "Adamant Bar"),
                            (125, "Rune Bar"),
                            (150, "Dragon Bar"),
                            (200, "Onyx"),
                            (250, "Zenyte")
                        ]

                        # Determine the new rank based on total points
                        new_rank = None
                        for threshold, rank in rank_thresholds:
                            if df.at[index, 'Total Points'] >= threshold:
                                new_rank = rank
                            else:
                                break

                        # Check if the rank has changed
                        if df.at[index, 'rank'] != new_rank:
                            df.at[index, 'rank'] = new_rank
                            rank_up_message = f"{df.at[index, 'rsn']} has been promoted to {new_rank}!"
                        else:
                            rank_up_message = None

                        # Save the DataFrame back to the CSV
                        df.to_csv(csv_file, index=False)

                        response_message = f"Added 5 points to '{df.at[index, 'rsn']}'. New total: {df.at[index, 'Total Points']}"
                        if rank_up_message:
                            response_message += f"\n{rank_up_message}"

                        await message.channel.send(response_message)
                    else:
                        await message.channel.send(f"RSN '{rsn}' not found in the clan list.")
                except Exception as e:
                    await message.channel.send(f"An error occurred: {str(e)}")
            else:
                await message.channel.send("You do not have permission to use this command.")
        # Add Joker Points End

        if message.content.startswith('!reactrole') and message.author != bot.user:
            # Check if the user has the admin role
            if any(role.id == admin_role_id for role in message.author.roles):
                try:
                    parts = message.content.split()

                    # Check for the --remove and --remove-message flags
                    remove_from_list = "--remove" in parts
                    remove_entire_message = "--remove-message" in parts

                    if remove_from_list:
                        # If --remove is present, we expect only 3 arguments
                        if len(parts) != 4:
                            raise ValueError("Invalid command format for removing a reaction.")

                        message_id = int(parts[1])
                        emoji = parts[2]

                        # Fetch the target message
                        target_message = await message.channel.fetch_message(message_id)

                        # Remove the reaction and its mapping
                        if str(message_id) in reaction_role_mapping:
                            if emoji in reaction_role_mapping[str(message_id)]["mappings"]:
                                del reaction_role_mapping[str(message_id)]["mappings"][emoji]
                                save_data(reaction_role_mapping)
                                await message.channel.send(
                                    f"Successfully removed reaction {emoji} from message {message_id}.")
                            else:
                                await message.channel.send(
                                    f"No reaction role mapping found for emoji {emoji} on message {message_id}.")
                        else:
                            await message.channel.send(f"No reaction roles are set up for message {message_id}.")

                    elif remove_entire_message:
                        # If --remove-message is present, we expect only 2 arguments
                        if len(parts) != 3:
                            raise ValueError("Invalid command format for removing a message.")

                        message_id = int(parts[1])

                        # Remove the entire message and its mappings
                        if str(message_id) in reaction_role_mapping:
                            del reaction_role_mapping[str(message_id)]
                            save_data(reaction_role_mapping)
                            await message.channel.send(
                                f"Successfully removed message {message_id} and all its reaction role mappings.")
                        else:
                            await message.channel.send(f"No reaction roles are set up for message {message_id}.")

                    else:
                        # If neither flag is present, handle it as before (adding/updating a reaction)
                        if len(parts) < 4 or len(parts) > 5:
                            raise ValueError("Invalid command format.")

                        message_id = int(parts[1])
                        emoji = parts[2]
                        role_to_add_mention = parts[3]

                        role_to_remove_mention = None
                        role_to_remove = None  # Initialize role_to_remove to None
                        role_to_remove_id = None  # Initialize role_to_remove_id to None
                        if len(parts) == 5 and parts[4].startswith("<@&"):
                            role_to_remove_mention = parts[4]

                        role_to_add_id = int(role_to_add_mention[3:-1])
                        role_to_add = message.guild.get_role(role_to_add_id)

                        if role_to_remove_mention:
                            role_to_remove_id = int(role_to_remove_mention[3:-1])
                            role_to_remove = message.guild.get_role(role_to_remove_id)

                        target_message = await message.channel.fetch_message(message_id)

                        # Add the reaction to the target message
                        await target_message.add_reaction(emoji)

                        # If the message ID is not in the mapping, create a new entry
                        if str(message_id) not in reaction_role_mapping:
                            reaction_role_mapping[str(message_id)] = {
                                "mappings": {},
                                "guild_id": message.guild.id,
                                "channel_id": message.channel.id
                            }

                        # Add or update the mapping for this emoji and roles
                        reaction_role_mapping[str(message_id)]["mappings"][emoji] = {
                            "add": role_to_add.id,
                            "remove": role_to_remove_id  # Can be None
                        }

                        save_data(reaction_role_mapping)

                        success_message = f"Successfully added {emoji} to message {message_id} and mapped it to add role {role_to_add.name}."
                        if role_to_remove:
                            success_message += f" Also mapped it to remove role {role_to_remove.name}."
                        await message.channel.send(success_message)

                except ValueError as e:
                    # Update the error message to include the new flag
                    await message.channel.send(
                        f"Invalid command format. Use one of the following:\n"
                        f"`!reactrole <message_id> <emoji> <@role_to_add> [<@role_to_remove>]`\n"
                        f"`!reactrole <message_id> <emoji> --remove`\n"
                        f"`!reactrole <message_id> --remove-message`\n"
                        f"Error: {e}")
                except discord.NotFound:
                    await message.channel.send("Message or role not found!")
                except discord.HTTPException as e:
                    await message.channel.send(f"An error occurred: {e}")
            else:
                await message.channel.send("You do not have permission to use this command.")
    # End of Reaction Role Management
        if content_lower.startswith('!addcommand') and any(role.id == admin_role_id for role in message.author.roles):
            try:
                parts = message.content.split(' ', 2)
                if len(parts) < 3:
                    await message.channel.send("Usage: !addcommand <command_name> <response>")
                    return

                command_name = parts[1].lower()
                response = parts[2]

                custom_commands[command_name] = response
                save_custom_commands()
                await message.channel.send(f"Custom command '{command_name}' added successfully.")
            except Exception as e:
                await message.channel.send(f"An error occurred: {e}")

        # Remove custom command
        elif content_lower.startswith('!removecommand') and any(role.id == admin_role_id for role in message.author.roles):
            try:
                parts = message.content.split(' ', 1)
                if len(parts) < 2:
                    await message.channel.send("Usage: !removecommand <command_name>")
                    return

                command_name = parts[1].lower()

                if command_name in custom_commands:
                    del custom_commands[command_name]
                    save_custom_commands()
                    await message.channel.send(f"Custom command '{command_name}' removed successfully.")
                else:
                    await message.channel.send(f"Custom command '{command_name}' not found.")
            except Exception as e:
                await message.channel.send(f"An error occurred: {e}")

        if content_lower.startswith('!editcommand') and any(role.id == admin_role_id for role in message.author.roles):
            try:
                parts = message.content.split(' ', 2)
                if len(parts) < 3:
                    await message.channel.send("Usage: !editcommand <command_name> <new_response>")
                    return

                command_name = parts[1].lower()
                new_response = parts[2]

                if command_name in custom_commands:
                    custom_commands[command_name] = new_response
                    save_custom_commands()
                    await message.channel.send(f"Custom command '{command_name}' edited successfully.")
                else:
                    await message.channel.send(f"Custom command '{command_name}' not found.")
            except Exception as e:
                await message.channel.send(f"An error occurred: {e}")

        if content_lower.startswith('!customcommands') and any(role.id == admin_role_id for role in message.author.roles):
            try:
                if custom_commands:
                    embed = discord.Embed(title="Custom Commands", color=discord.Color.blue())
                    for cmd in custom_commands.keys():
                        embed.add_field(name=cmd, value="\u200b", inline=False)
                    await message.channel.send(embed=embed)
                else:
                    await message.channel.send("No custom commands found.")
            except Exception as e:
                await message.channel.send(f"An error occurred: {e}")

        # Handle custom commands
        else:
            for command, response in custom_commands.items():
                if re.search(r'\b' + re.escape(command) + r'\b', content_lower) and not message.author.bot:
                    await message.channel.send(response)
                    break

        if content_lower.startswith('!memberlist') and not message.author.bot:
            csv_file = DATA_DIR / "fools_union_member_data.csv"
            df = pd.read_csv(csv_file, dtype={'Discord': str})

            rank_thresholds = [
                (0, "Bronze Bar"),
                (10, "Iron Bar"),
                (30, "Steel Bar"),
                (50, "Gold Bar"),
                (75, "Mithril Bar"),
                (100, "Adamant Bar"),
                (125, "Rune Bar"),
                (150, "Dragon Bar"),
                (200, "Onyx"),
                (250, "Zenyte")
            ]
            for threshold, rank in rank_thresholds:
                if total_points < threshold:
                    return rank
            return "Zenyte"

            user_data = "RSN | Rank | Points Until Next Rank\n"
            user_data += "----|------|----------------------\n"

            for index, row in df.iterrows():
                rsn = row['rsn']
                rank = row['rank']
                total_points = row['Total Points']

                next_rank = None
                points_needed = None
                for threshold, rank_name in rank_thresholds:
                    if total_points < threshold:
                        next_rank = rank_name
                        points_needed = threshold - total_points
                        break

                if next_rank is None:
                    points_needed = 0  # Already at the highest rank

                user_data += f"{rsn} | {rank} | {points_needed}\n"

            await message.channel.send(f"```{user_data}```")

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

    # Reaction events
    async def handle_reaction(payload, add_or_remove):
        guild = bot.get_guild(payload.guild_id)
        if not guild:
            print(f"Guild {payload.guild_id} not found.")
            return

        reactions = reaction_role_mapping.get(str(payload.message_id))
        if not reactions:
            return

        for emoji, role_data in reactions["mappings"].items():
            if str(payload.emoji) == emoji:
                role_to_add = guild.get_role(role_data["add"])
                role_to_remove = guild.get_role(role_data["remove"]) if role_data["remove"] else None

                member = guild.get_member(payload.user_id)
                if not member:
                    print(f"Member {payload.user_id} not found.")
                    return

                try:
                    if add_or_remove == "add":
                        await member.add_roles(role_to_add)
                        if role_to_remove:
                            await member.remove_roles(role_to_remove)
                        print(f"Added role {role_to_add.name} to {member.name}")
                    elif add_or_remove == "remove":
                        await member.remove_roles(role_to_add)
                        print(f"Removed role {role_to_add.name} from {member.name}")
                except discord.Forbidden:
                    print(f"Bot doesn't have permission to manage roles for {member.name}")
                except discord.HTTPException as e:
                    print(f"Failed to manage roles due to an error: {e}")

    @bot.event
    async def on_raw_reaction_add(payload):
        await handle_reaction(payload, "add")

    @bot.event
    async def on_raw_reaction_remove(payload):
        await handle_reaction(payload, "remove")

#Start MakeAVC
TARGET_VOICE_CHANNEL_ID = int(vc_id)

    # Dictionary to store created channels for each user
created_channels = {}

    # Path to store JSON data
json_file_path = DATA_DIR / "created_channels.json"


# Function to load created channels from JSON
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

# Load the created channels from the JSON file when the bot starts
load_channels_from_json()

# Check if the channels still exist and delete the ones that are empty
async def check_and_delete_empty_channels():
    for guild in bot.guilds:
        for user_id, channel_id in list(created_channels.items()):
            channel = guild.get_channel(channel_id)
            if channel and len(channel.members) == 0:
                await channel.delete()
                del created_channels[user_id]
    save_channels_to_json()

@bot.event
async def on_voice_state_update(member, before, after):
    if after.channel and after.channel.id == TARGET_VOICE_CHANNEL_ID:
        # User joined the target voice channel

        # Check if the user already has a created channel
        if member.id in created_channels:
            existing_channel_id = created_channels[member.id]
            existing_channel = member.guild.get_channel(existing_channel_id)
            if existing_channel:
                await member.move_to(existing_channel)
                print(f"Moved {member.name} to their existing channel: {existing_channel.name}")
                return

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
    # End MakeAVC
bot.run(bot_token)