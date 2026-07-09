import pandas as pd
import sqlite3

print("Connecting to github_analytics.db...")
conn = sqlite3.connect("github_analytics.db")

# Step 1 - Load only the columns we need from the cleaned events table
print("Loading events (repo, ecosystem, year_month, is_bot)...")
df = pd.read_sql(
    "SELECT repo, ecosystem, year_month, is_bot FROM events",
    conn
)
conn.close()
print("Loaded rows:", len(df))

# Step 2 - Group by repo, ecosystem, month, and bot/human, then count events
print("Grouping and counting bot vs human activity...")
bot_activity = (
    df.groupby(["repo", "ecosystem", "year_month", "is_bot"])
      .size()
      .reset_index(name="event_count")
)
print("Rows in output table:", len(bot_activity))

# Step 3 - Sanity checks against known totals from the data overview doc
total_bot = bot_activity.loc[bot_activity.is_bot == True, "event_count"].sum()
total_human = bot_activity.loc[bot_activity.is_bot == False, "event_count"].sum()
total_all = bot_activity["event_count"].sum()

print("Total bot events:", total_bot)      # expected ~848,909
print("Total human events:", total_human)  # expected ~2,599,517
print(f"Bot percentage: {100 * total_bot / total_all:.2f}%")  # expected ~24.62%

# Step 4 - Preview before saving
print(bot_activity.head(10))

# Step 5 - Save output CSV
output_path = "features/bot_activity.csv"
bot_activity.to_csv(output_path, index=False)
print("Saved:", output_path)

print("DONE")