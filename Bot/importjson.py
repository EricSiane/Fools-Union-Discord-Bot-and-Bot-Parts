# importjson.py
import os
import json
import pathlib

DATA_DIR = pathlib.Path("data")

def handle_storedata_command(data_to_import):
    try:
        imported_data = json.loads(data_to_import)

        for entry in imported_data:
            for key, value in entry.items():
                if isinstance(value, str):
                    entry[key] = value.rstrip()

        try:
            with open(DATA_DIR / 'clan_member_data.json', 'r') as f:
                existing_data = json.load(f)

            for entry in existing_data:
                for key, value in entry.items():
                    if isinstance(value, str):
                        entry[key] = value.rstrip()
        except FileNotFoundError:
            existing_data = []

        existing_data.extend(imported_data)
        with open(DATA_DIR / 'clan_member_data.json', 'w') as f:
            json_str = json.dumps(existing_data, indent=4)
            f.write(json_str.rstrip() + "\n")

        return "Data imported successfully!"
    except json.JSONDecodeError:
        return "Error: Invalid JSON data provided."


async def handle_importjson_command(message, admin_role_id):
    if not any(role.id == admin_role_id for role in message.author.roles):
        await message.channel.send("You do not have permission to use this command.")
        return

    if message.attachments:
        attachment = message.attachments[0]
        if attachment.filename.endswith('.json'):
            try:
                json_data = await attachment.read()
                data = json.loads(json_data.decode('utf-8'))

                # Save the data to clan_member_data.json
                with open('clan_member_data.json', 'w') as f:
                    json.dump(data, f, indent=4)

                await message.channel.send("JSON data imported and saved successfully.")
            except json.JSONDecodeError:
                await message.channel.send("Error: Invalid JSON data provided.")
            except Exception as e:
                await message.channel.send(f"An unexpected error occurred: {e}")
        else:
            await message.channel.send("Error: The attached file is not a JSON file.")
    else:
        await message.channel.send("Error: No file attached.")