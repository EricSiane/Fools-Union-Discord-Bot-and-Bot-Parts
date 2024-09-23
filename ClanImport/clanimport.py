import json
import pandas as pd
import argparse

from datetime import datetime


def load_data(json_string):
    """Loads member data from a JSON string."""
    return json.loads(json_string)


def calculate_member_stats(members):
    """Calculates additional stats for each member."""
    today = datetime.today()
    for member in members:
        joined_date = datetime.strptime(member["joinedDate"], "%d-%b-%Y")
        days_elapsed = (today - joined_date).days
        member["days in clan"] = days_elapsed
        member["points from time in clan"] = (days_elapsed // 5)
        member["joinedDate"] = joined_date.strftime("%#m/%#d/%Y")  # Format date
    return members


def update_clan_csv(clan_csv, members):
    """Updates the clan CSV with member data."""
    for member in members:
        # Check if member exists in CSV
        existing_member = clan_csv[clan_csv['rsn'].str.rstrip() == member['rsn'].rstrip()]

        if not existing_member.empty:
            # Update existing member
            index = existing_member.index[0]
            clan_csv.at[index, 'Points From Time in Clan'] = member["points from time in clan"]
            clan_csv.at[index, 'Days in Clan'] = member["days in clan"]
        else:
            # Add new member
            clan_csv.loc[len(clan_csv)] = [
                member['rsn'],
                member["joinedDate"],
                "Bronze Bar",
                "",
                member["days in clan"],
                member["points from time in clan"],
                0,
                member["points from time in clan"],
                []
            ]
    return clan_csv


def update_ranks(clan_csv):
    """Updates ranks based on total points."""

    def get_new_rank(total_points):
        """Determines the new rank based on total points."""
        rank_thresholds = [
            (10, "Bronze Bar"),
            (30, "Iron Bar"),
            (50, "Steel Bar"),
            (75, "Gold Bar"),
            (100, "Mithril Bar"),
            (125, "Adamant Bar"),
            (150, "Rune Bar"),
            (200, "Dragon Bar"),
            (250, "Onyx"),
        ]
        for threshold, rank in rank_thresholds:
            if total_points < threshold:
                return rank
        return "Zenyte"

    # Calculate total points and update ranks efficiently using pandas apply
    clan_csv['Total Points'] = clan_csv['Points From Time in Clan'] + clan_csv['Other Points']
    clan_csv['new_rank'] = clan_csv['Total Points'].apply(get_new_rank)

    # Identify and print rank changes
    rank_changed = clan_csv['rank'] != clan_csv['new_rank']
    for _, row in clan_csv[rank_changed].iterrows():
        print(f"{row['rsn']} rank has changed to: {row['new_rank']}")

    # Update the 'rank' column
    clan_csv['rank'] = clan_csv['new_rank']
    clan_csv.drop(columns=['new_rank'], inplace=True)  # Remove temporary column

    print("Updated!")
    return clan_csv


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-csv", help="masterlist csv file of clan members")
    parser.add_argument("-json_data", help="JSON data of clan members")
    args = parser.parse_args()

    # Load data
    with open(args.json_data, 'r') as f:
        json_data = f.read()

    members = load_data(json_data)
    members = calculate_member_stats(members)
    clan_csv = pd.read_csv(args.csv)
    clan_csv['rsn'] = clan_csv['rsn'].astype(str)

    # Update CSV and ranks
    clan_csv = update_clan_csv(clan_csv, members)
    clan_csv = update_ranks(clan_csv)

    # Save updated CSV
    clan_csv.to_csv(args.csv, index=False)


if __name__ == "__main__":
    main()