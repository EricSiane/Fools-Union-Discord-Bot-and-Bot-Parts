import asyncio
import discord
import pathlib
import pandas as pd
import json
from datetime import datetime

DATA_DIR = pathlib.Path("data")
csv_file = DATA_DIR / "fools_union_member_data.csv"
json_file = DATA_DIR / "user_not_in_clan.json"

async def handle_rsn_command(message, bot, guild, ANNOUNCEMENT_CHANNEL_ID):
    rsn = message.content[len('!rsn '):]  # Keep the original case

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

    df['Discord'] = df['Discord'].astype(str)
    df['rsn_lower'] = df['rsn'].str.lower()
    fools = discord.utils.get(guild.roles, name="Fools")
    iron = discord.utils.get(guild.roles, name="Iron Bar")
    guest = discord.utils.get(guild.roles, name="Guest")
    joiner = discord.utils.get(guild.roles, name="Joiner")

    if rsn.lower() in df['rsn_lower'].values:
        index = df.index[df['rsn_lower'] == rsn.lower()].tolist()[0]
        df.at[index, 'Discord'] = str(message.author.id)

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
            f"Discord ID {message.author.mention} has been linked to RSN '{original_rsn}'."
        )
        await message.author.add_roles(fools, iron)
        await message.author.remove_roles(guest, joiner)

        await asyncio.sleep(10)  # Wait for 10 seconds
        try:
            await sent_message.delete()
        except discord.NotFound:
            print("Message already deleted.")
        try:
            await message.delete()
        except discord.NotFound:
            print("Message already deleted.")

        try:
            await message.author.edit(nick=original_rsn)
        except discord.Forbidden:
            await message.channel.send("I don't have permission to change your nickname.")
        except discord.HTTPException as e:
            await message.channel.send(f"Failed to change nickname: {e}")
    else:
        # Add or update the RSN and Discord ID in user_not_in_clan.json
        user_data = {
            "rsn": rsn,
            "discord_id": str(message.author.id)
        }

        if json_file.exists() and json_file.stat().st_size != 0:
            with open(json_file, 'r') as f:
                data = json.load(f)
        else:
            data = []

        # Check if the user ID already exists
        user_exists = False
        for user in data:
            if user['discord_id'] == str(message.author.id):
                user['rsn'] = rsn  # Update the RSN
                user_exists = True
                break

        if not user_exists:
            data.append(user_data)

        with open(json_file, 'w') as f:
            json.dump(data, f, indent=4)

        sent_message = await message.channel.send(
            f"RSN '{rsn}' not found in the clan list. If you aren't in the clan, welcome as a guest!")
        await message.author.add_roles(guest)
        await message.author.remove_roles(joiner)
        try:
            await message.author.edit(nick=rsn)  # Change nickname to the entered RSN
        except discord.Forbidden:
            await message.channel.send("I don't have permission to change your nickname.")
        except discord.HTTPException as e:
            await message.channel.send(f"Failed to change nickname: {e}")

        await asyncio.sleep(10)  # Wait for 10 seconds
        try:
            await sent_message.delete()
        except discord.NotFound:
            print("Message already deleted.")
        try:
            await message.delete()
        except discord.NotFound:
            print("Message already deleted.")