import os
import csv
import discord
from discord.ext import commands
import asyncio
import pathlib
from dotenv import load_dotenv

load_dotenv()
DATA_DIR = pathlib.Path("data")
CSV_PATH = DATA_DIR / "fools_union_member_data.csv"

# Dictionary to map clan ranks to Discord role names
RANK_TO_ROLE = {
    "Bronze Bar": "Bronze Bar",
    "Iron Bar": "Iron Bar",
    "Steel Bar": "Steel Bar",
    "Gold Bar": "Gold Bar",
    "Mithril Bar": "Mithril Bar",
    "Adamant Bar": "Adamant Bar",
    "Rune Bar": "Rune Bar",
    "Dragon Bar": "Dragon Bar",
    "Onyx": "Onyx",
    "Zenyte": "Zenyte",
    # Add more ranks as needed
}


async def update_member_ranks(bot, guild_id=None):
    """
    Update Discord roles based on the ranks in the CSV file.

    Args:
        bot: The Discord bot instance
        guild_id: Optional guild ID to target a specific server
    """
    print("Starting rank update process...")

    if not os.path.exists(CSV_PATH):
        print(f"Error: CSV file not found at {CSV_PATH}")
        return

    # Get the guild
    if guild_id:
        guild = bot.get_guild(int(guild_id))
    else:
        guild = bot.guilds[0] if bot.guilds else None

    if not guild:
        print("Error: No guild available")
        return

    # Prepare roles dictionary
    role_dict = {role.name: role for role in guild.roles}
    for rank_name, role_name in RANK_TO_ROLE.items():
        if role_name not in role_dict:
            print(f"Warning: Role '{role_name}' not found in the server")

    # Read CSV and update roles
    members_updated = 0
    members_not_found = 0

    try:
        with open(CSV_PATH, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                # Skip if Discord ID is not available
                if row['Discord'] == 'nan' or not row['Discord']:
                    continue

                try:
                    discord_id = int(row['Discord'])
                    member = guild.get_member(discord_id)

                    if not member:
                        members_not_found += 1
                        continue

                    rank = row['rank']
                    if rank in RANK_TO_ROLE:
                        role_name = RANK_TO_ROLE[rank]
                        if role_name in role_dict:
                            # Get the roles to add and remove
                            role_to_add = role_dict[role_name]
                            roles_to_remove = [role_dict[r] for r in RANK_TO_ROLE.values()
                                               if r in role_dict and r != role_name]

                            # Remove other rank roles
                            for role in roles_to_remove:
                                if role in member.roles:
                                    await member.remove_roles(role)

                            # Add the correct rank role
                            if role_to_add not in member.roles:
                                await member.add_roles(role_to_add)
                                print(f"Updated {member.name}'s rank to {role_name}")
                                members_updated += 1

                except ValueError:
                    print(f"Invalid Discord ID format for {row['rsn']}")
                except Exception as e:
                    print(f"Error updating {row.get('rsn', 'unknown')}: {str(e)}")

    except Exception as e:
        print(f"Error reading CSV file: {str(e)}")
        return

    print(f"Rank update complete: {members_updated} members updated, {members_not_found} members not found in server")
    return members_updated, members_not_found


async def handle_rank_update_command(message, admin_role_id):
    """
    Handle the !rankupdate command to manually trigger rank updates
    """
    if not admin_role_id:
        await message.channel.send("Admin role is not configured.")
        return

    # Check if the user has the admin role
    admin_role = discord.utils.get(message.guild.roles, id=admin_role_id)
    if admin_role not in message.author.roles:
        await message.channel.send("You don't have permission to use this command.")
        return

    try:
        status_message = await message.channel.send("Updating member ranks...")

        # Get the bot instance directly
        bot = message.guild.me._state._get_client()

        # Call update_member_ranks with the correct parameters
        updated, not_found = await update_member_ranks(bot, message.guild.id)

        await status_message.edit(
            content=f"Rank update complete: {updated} members updated, {not_found} members not found in server.")

    except Exception as e:
        error_message = str(e)
        print(f"Error in rank update: {error_message}")
        await message.channel.send(f"Error during rank update: {error_message}")


# This function can be scheduled to run periodically
async def scheduled_rank_update(bot):
    """Run rank updates on a schedule"""
    while True:
        for guild in bot.guilds:
            await update_member_ranks(bot, guild.id)
        # Run every day (86400 seconds)
        await asyncio.sleep(86400)