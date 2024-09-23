import discord
import random
from collections import deque
import json
import os

# Create an instance of Intents and enable the message content intent
intents = discord.Intents.default()
intents.message_content = True  # Required to read message content
# Lists for randomization
skill_of_the_week = ["Runecraft", "Construction", "Agility", "Herblore", "Thieving", "Crafting", "Fletching", "Slayer", "Hunter", "Mining", "Smithing", "Fishing", "Cooking", "Firemaking", "Woodcutting", "Farming"]


boss_of_the_week = ["Abyssal Sire", "Alchemical Hydra", "Araxxor", "Barrows", "Bryophyta", "Callisto", "Vet'ion", "Cerberus", "Chaos Elemental", "Chaos Fanatic", "Commander Zilyana", "Corporeal Beast", "Crazy Archaeologist", "Dagannoth Prime", "Dagannoth Rex", "Dagannoth Supreme",
 "Deranged Archaeologist", "Duke Sucellus", "General Graardor", "Giant Mole", "Grotesque Guardians",
 "Kalphite Queen", "King Black Dragon", "Kraken", "Kree'Arra", "K'ril Tsutsaroth", "Nex", "Nightmare", "Obor", "Phantom Muspah", "Sarachnis", "Scorpia", "Scurrius", "Skotizo", "Tempoross", "The Gauntlet", "The Leviathan", "The Whisperer", "Thermonuclear Smoke Devil", "TzTok-Jad", "Vardorvis", "Venenatis", "Vorkath", "Wintertodt", "Zalcano", "Zulrah"]

data_file_path = 'selection_data.json'

# Load data if it exists
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

bot = discord.Client(intents=intents)  # Adjust intents as needed
PREFIX = "!"

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.content.startswith(PREFIX):
        command = message.content[len(PREFIX):].strip()


        if command == "rs" or command == "randomskill":
            # Choose boss, ensuring it's not in the last 3
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

bot.run(TOKEN)  # Replace with your actual bot token