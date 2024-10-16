import pandas as pd
import pathlib

DATA_DIR = pathlib.Path("data")

async def handle_points_command(message):
    content_lower = message.content.lower()
    rsn = content_lower[len('!points '):].strip().lower()

    csv_file = DATA_DIR / "fools_union_member_data.csv"
    df = pd.read_csv(csv_file, dtype={'Discord': str})

    df['rsn_lower'] = df['rsn'].str.lower()

    if rsn in df['rsn_lower'].values:
        index = df.index[df['rsn_lower'] == rsn].tolist()[0]
        discord_value = df.at[index, 'Discord']
        discord_linked = not pd.isna(discord_value) and discord_value != '' and discord_value != 0
        time_in_clan = df.at[index, 'Days in Clan']
        other_points = df.at[index, 'Other Points']
        total_points = df.at[index, 'Total Points']

        # Define rank thresholds
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

        # Determine the current rank
        current_rank = "Bronze Bar"
        for threshold, rank in rank_thresholds:
            if total_points >= threshold:
                current_rank = rank
            else:
                break

        # Determine the next rank and points needed
        next_rank = None
        points_needed = None
        for threshold, rank in rank_thresholds:
            if total_points < threshold:
                next_rank = rank
                points_needed = threshold - total_points
                break

        await message.channel.send(
            f"RSN: {df.at[index, 'rsn']}\n"
            f"Discord Linked: {'Yes' if discord_linked else 'No'}\n"
            f"Time in Clan: {time_in_clan} days\n"
            f"Other Points: {other_points}\n"
            f"Total Points: {total_points}\n"
            f"Current Rank: {current_rank}\n"
            f"Next Rank: {next_rank}\n"
            f"Points Needed for Next Rank: {points_needed}"
        )
    else:
        await message.channel.send(f"RSN '{rsn}' not found in the clan list.")