# reactrole.py
import discord
import json
import pathlib
from shared import reaction_role_mapping, save_role_data, load_role_data


DATA_DIR = pathlib.Path("data")

async def handle_reactrole_command(message, admin_role_id, reaction_role_mapping, save_data):
    if any(role.id == admin_role_id for role in message.author.roles):
        try:
            parts = message.content.split()

            remove_from_list = "--remove" in parts
            remove_entire_message = "--remove-message" in parts

            if remove_from_list:
                if len(parts) != 4:
                    raise ValueError("Invalid command format for removing a reaction.")

                message_id = int(parts[1])
                emoji = parts[2]

                target_message = await message.channel.fetch_message(message_id)

                if str(message_id) in reaction_role_mapping:
                    if emoji in reaction_role_mapping[str(message_id)]["mappings"]:
                        del reaction_role_mapping[str(message_id)]["mappings"][emoji]
                        save_data(reaction_role_mapping)
                        await message.channel.send(f"Successfully removed reaction {emoji} from message {message_id}.")
                    else:
                        await message.channel.send(f"No reaction role mapping found for emoji {emoji} on message {message_id}.")
                else:
                    await message.channel.send(f"No reaction roles are set up for message {message_id}.")

            elif remove_entire_message:
                if len(parts) != 3:
                    raise ValueError("Invalid command format for removing a message.")

                message_id = int(parts[1])

                if str(message_id) in reaction_role_mapping:
                    del reaction_role_mapping[str(message_id)]
                    save_data(reaction_role_mapping)
                    await message.channel.send(f"Successfully removed message {message_id} and all its reaction role mappings.")
                else:
                    await message.channel.send(f"No reaction roles are set up for message {message_id}.")

            else:
                if len(parts) < 4 or len(parts) > 5:
                    raise ValueError("Invalid command format.")

                message_id = int(parts[1])
                emoji = parts[2]
                role_to_add_mention = parts[3]

                role_to_remove_mention = None
                role_to_remove = None
                role_to_remove_id = None
                if len(parts) == 5 and parts[4].startswith("<@&"):
                    role_to_remove_mention = parts[4]

                role_to_add_id = int(role_to_add_mention[3:-1])
                role_to_add = message.guild.get_role(role_to_add_id)

                if role_to_remove_mention:
                    role_to_remove_id = int(role_to_remove_mention[3:-1])
                    role_to_remove = message.guild.get_role(role_to_remove_id)

                target_message = await message.channel.fetch_message(message_id)

                await target_message.add_reaction(emoji)

                if str(message_id) not in reaction_role_mapping:
                    reaction_role_mapping[str(message_id)] = {
                        "mappings": {},
                        "guild_id": message.guild.id,
                        "channel_id": message.channel.id
                    }

                reaction_role_mapping[str(message_id)]["mappings"][emoji] = {
                    "add": role_to_add.id,
                    "remove": role_to_remove_id
                }

                save_data(reaction_role_mapping)

                success_message = f"Successfully added {emoji} to message {message_id} and mapped it to add role {role_to_add.name}."
                if role_to_remove:
                    success_message += f" Also mapped it to remove role {role_to_remove.name}."
                await message.channel.send(success_message)

        except ValueError as e:
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
    save_role_data(reaction_role_mapping)


async def assign_or_remove_roles_for_existing_reactions(bot, reaction_role_mapping):
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

async def handle_reaction(bot, payload, add_or_remove):
    print(f"Handling reaction: {add_or_remove} for message ID: {payload.message_id}")
    reactions = reaction_role_mapping.get(str(payload.message_id))
    guild = bot.get_guild(payload.guild_id)
    if not guild:
        print(f"Guild {payload.guild_id} not found.")
        return

    if not reactions:
        print(f"No reactions found for message ID: {payload.message_id}")
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
                    if role_to_add:
                        await member.add_roles(role_to_add)
                        print(f"Added role {role_to_add.name} to {member.name}")
                    if role_to_remove:
                        await member.remove_roles(role_to_remove)
                        print(f"Removed role {role_to_remove.name} from {member.name}")
                elif add_or_remove == "remove":
                    if role_to_add:
                        await member.remove_roles(role_to_add)
                        print(f"Removed role {role_to_add.name} from {member.name}")
            except discord.Forbidden:
                print(f"Bot doesn't have permission to manage roles for {member.name}")
            except discord.HTTPException as e:
                print(f"Failed to manage roles due to an error: {e}")

async def on_raw_reaction_add(bot, payload):
    await handle_reaction(bot, payload, "add")

async def on_raw_reaction_remove(bot, payload):
    await handle_reaction(bot, payload, "remove")

reaction_role_mapping = load_role_data()
