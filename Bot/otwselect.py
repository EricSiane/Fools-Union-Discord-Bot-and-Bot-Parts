import os
import json
import random
from collections import deque
import pathlib

DATA_DIR = pathlib.Path("data")

async def handle_otwselect_command(message, admin_role_id, skill_of_the_week, boss_of_the_week):
    content_lower = message.content.lower()
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