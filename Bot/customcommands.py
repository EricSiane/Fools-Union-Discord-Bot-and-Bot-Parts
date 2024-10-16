# custom_commands.py
import discord
import json
import pathlib
import re

DATA_DIR = pathlib.Path("data")
custom_commands = {}

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

async def handle_add_command(message, admin_role_id):
    if any(role.id == admin_role_id for role in message.author.roles):
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

async def handle_remove_command(message, admin_role_id):
    if any(role.id == admin_role_id for role in message.author.roles):
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

async def handle_edit_command(message, admin_role_id):
    if any(role.id == admin_role_id for role in message.author.roles):
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

async def handle_list_commands(message, admin_role_id):
    if any(role.id == admin_role_id for role in message.author.roles):
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

async def handle_custom_command(message):
    content_lower = message.content.lower()
    for command, response in custom_commands.items():
        if re.search(r'\b' + re.escape(command) + r'\b', content_lower) and not message.author.bot:
            await message.channel.send(response)
            break