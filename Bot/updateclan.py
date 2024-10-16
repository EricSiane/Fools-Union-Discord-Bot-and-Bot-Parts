# updateclan.py
import json
import pandas as pd
from datetime import datetime
import pathlib

DATA_DIR = pathlib.Path("data")

async def run_clan_update(message, admin_role_id):
    JSON_FILE = DATA_DIR / "clan_member_data.json"
    csv_file = DATA_DIR / "fools_union_member_data.csv"

    def load_data(json_file):
        with open(json_file, 'r') as f:
            data = json.load(f)
        return data

    def calculate_member_stats(members):
        today = datetime.today()
        for member in members:
            joined_date = datetime.strptime(member["joinedDate"], "%d-%b-%Y")
            days_elapsed = (today - joined_date).days
            member["days in clan"] = days_elapsed
            member["points from time in clan"] = (days_elapsed // 5)
            member["joinedDate"] = joined_date.strftime("%#m/%#d/%Y")
        return members

    def update_clan_csv(clan_csv, members):
        if 'Discord Points' not in clan_csv.columns:
            clan_csv['Discord Points'] = 0

        for member in members:
            existing_member = clan_csv[clan_csv['rsn'].str.rstrip() == member['rsn'].rstrip()]

            if not existing_member.empty:
                index = existing_member.index[0]
                clan_csv.at[index, 'Points From Time in Clan'] = member["points from time in clan"]
                clan_csv.at[index, 'Days in Clan'] = member["days in clan"]
                if pd.notna(clan_csv.at[index, 'Discord']) and clan_csv.at[index, 'Discord'] != '' and \
                        clan_csv.at[index, 'Discord Points'] < 10:
                    clan_csv.at[index, 'Discord Points'] += 10
            else:
                new_member = pd.DataFrame([{
                    'rsn': member['rsn'],
                    'joinedDate': member["joinedDate"],
                    'rank': "Bronze Bar",
                    'Discord': "",
                    'Days in Clan': member["days in clan"],
                    'Points From Time in Clan': member["points from time in clan"],
                    'Other Points': 0,
                    'Discord Points': 0,
                    'Total Points': member["points from time in clan"],
                    'Alts': [],
                    'rsn_lower': []
                }])
                clan_csv = pd.concat([clan_csv, new_member], ignore_index=True)
        return clan_csv

    async def update_ranks(clan_csv):
        def get_new_rank(total_points):
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

        clan_csv['Total Points'] = clan_csv['Points From Time in Clan'] + clan_csv['Other Points'] + \
                                   clan_csv['Discord Points']
        clan_csv['new_rank'] = clan_csv['Total Points'].apply(get_new_rank)

        rank_changes = []
        rank_changed = clan_csv['rank'] != clan_csv['new_rank']
        for _, row in clan_csv[rank_changed].iterrows():
            rank_changes.append((row['rsn'], row['new_rank']))
            print(f"{row['rsn']} rank has changed to: {row['new_rank']}")

        clan_csv['rank'] = clan_csv['new_rank']
        clan_csv.drop(columns=['new_rank'], inplace=True)

        print("Updated!")
        return clan_csv, rank_changes

    async def main():
        members = load_data(JSON_FILE)
        members = calculate_member_stats(members)
        df = pd.read_csv(csv_file, dtype={'Discord': str})
        df['rsn'] = df['rsn'].astype(str)

        df = update_clan_csv(df, members)
        df, rank_changes = await update_ranks(df)

        df['Discord'] = df['Discord'].astype(str)
        df.to_csv(csv_file, index=False)

        if rank_changes:
            rank_up_messages = "\n".join(
                [f"{rsn} has been promoted to {new_rank}!" for rsn, new_rank in rank_changes])
            await message.channel.send(f"Rank Up Notifications:\n{rank_up_messages}")

    if any(role.id == admin_role_id for role in message.author.roles):
        await main()
        await message.channel.send(f"Clan has been updated!")
    else:
        await message.channel.send("You do not have permission to use this command.")