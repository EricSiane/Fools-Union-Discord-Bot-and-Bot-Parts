# export.py
import discord
import pathlib

DATA_DIR = pathlib.Path("data")

async def handle_export_command(message, admin_role_id):
    if any(role.id == admin_role_id for role in message.author.roles):
        try:
            file = discord.File(DATA_DIR / "fools_union_member_data.csv")
            await message.channel.send("Here is the file you requested:", file=file)
        except Exception as e:
            await message.channel.send(f"Failed to send file: {e}")
    else:
        await message.channel.send("You do not have permission to use this command.")