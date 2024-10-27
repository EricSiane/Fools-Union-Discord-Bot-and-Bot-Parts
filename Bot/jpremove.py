# jpadd.py
import pandas as pd
import pathlib

DATA_DIR = pathlib.Path("data")

async def handle_jpremove_command(message, admin_role_id):
    if any(role.id == admin_role_id for role in message.author.roles):
        csv_file = DATA_DIR / "fools_union_member_data.csv"
        df = pd.read_csv(csv_file, dtype={'Discord': str})
        try:
            content = message.content[len('!jpremove '):].strip().lower()
            rsn, points_str = content.rsplit(' ', 1)
            points = int(points_str)
            df['rsn_lower'] = df['rsn'].str.lower()

            if rsn in df['rsn_lower'].values:
                index = df.index[df['rsn_lower'] == rsn].tolist()[0]
                df.at[index, 'Other Points'] -= points
                df.at[index, 'Total Points'] = df.at[index, 'Points From Time in Clan'] + df.at[index, 'Other Points']

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

                new_rank = None
                for threshold, rank in rank_thresholds:
                    if df.at[index, 'Total Points'] >= threshold:
                        new_rank = rank
                    else:
                        break

                if df.at[index, 'rank'] != new_rank:
                    df.at[index, 'rank'] = new_rank
                else:
                    rank_up_message = None

                df['Discord'] = df['Discord'].astype(str)
                df.to_csv(csv_file, index=False)

                response_message = f"Removed {points} points from '{df.at[index, 'rsn']}'. New total: {df.at[index, 'Total Points']}"


                await message.channel.send(response_message)
            else:
                await message.channel.send(f"RSN '{rsn}' not found in the clan list.")
        except Exception as e:
            await message.channel.send(f"An error occurred: {str(e)}")
    else:
        await message.channel.send("You do not have permission to use this command.")