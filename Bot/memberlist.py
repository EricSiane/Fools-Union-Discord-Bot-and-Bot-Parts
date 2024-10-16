# memberlist.py
import pandas as pd
import pathlib

DATA_DIR = pathlib.Path("data")

async def handle_memberlist_command(message):
    csv_file = DATA_DIR / "fools_union_member_data.csv"
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

    user_data = "RSN | Rank | Points Until Next Rank\n"
    user_data += "----|------|----------------------\n"

    for index, row in df.iterrows():
        rsn = row['rsn']
        rank = row['rank']
        total_points = row['Total Points']

        next_rank = None
        points_needed = None
        for threshold, rank_name in rank_thresholds:
            if total_points < threshold:
                next_rank = rank_name
                points_needed = threshold - total_points
                break

        if next_rank is None:
            points_needed = 0  # Already at the highest rank

        user_data += f"{rsn} | {rank} | {points_needed}\n"

    await message.channel.send(f"```{user_data}```")