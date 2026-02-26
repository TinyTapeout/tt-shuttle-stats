import requests
import argparse
import json
import pandas as pd
from datetime import datetime, timezone
import matplotlib.pyplot as plt

parser = argparse.ArgumentParser(description="Plot Tiny Tapeout shuttle submission statistics")
parser.add_argument('--log', action='store_true', help="Use log scale (hours) on x-axis")
parser.add_argument('--dump', action='store_true', help="Dump the json data locally")
parser.add_argument('--show', action='store_true', help="Show the plot with matplotlib")
parser.add_argument('--shuttle-id', type=int, help="Force shuttle id")
args = parser.parse_args()

# Don't show these ones
skip_shuttles = [
    "Tiny Tapeout 4", "Tiny Tapeout 5", "Tiny Tapeout 10", "Tiny Tapeout CAD 25a",
    "Tiny Tapeout IHP 0p2", "Tiny Tapeout IHP 0p3",
    "Tiny Tapeout IHP 25a", "Tiny Tapeout Sky 25a", "Tiny Tapeout GF 0p2"
]

# Fetch JSON data from the API
url = "https://app.tinytapeout.com/api/shuttles/submission-stats"
response = requests.get(url)
response.raise_for_status()
data = response.json()

# Optionally, save it locally
if args.dump:
    with open("data.json", "w") as file:
        json.dump(data, file, indent=4)

# Extract shuttle info
shuttles = data['shuttles']
id_to_name = {item["id"]: item["name"] for item in shuttles}
shuttle_deadlines = {item["id"]: pd.to_datetime(item["deadline"]) for item in shuttles}
shuttle_tiles_total = {item["id"]: item["tiles_total"] for item in shuttles}

# Current UTC time
now_utc = pd.Timestamp(datetime.now(timezone.utc))

# Filter deadlines that are in the future
future_shuttles = {sid: dl for sid, dl in shuttle_deadlines.items() if dl >= now_utc}

if not future_shuttles:
    raise ValueError("No future shuttles found in the data")

# Find the shuttle with deadline closest to today
closest_shuttle_id = min(future_shuttles, key=lambda sid: abs(future_shuttles[sid] - now_utc))
closest_deadline = future_shuttles[closest_shuttle_id]

if args.shuttle_id:
    closest_shuttle_id = args.shuttle_id
print(f"Highlighting shuttle: {id_to_name[closest_shuttle_id]}, Deadline: {closest_deadline}")

# Automatically set log mode if within 7 days
days_to_deadline = (closest_deadline - now_utc).total_seconds() / (24*3600)
log_x = (days_to_deadline <= 7) or args.log

print(f"Log mode: {log_x} ({days_to_deadline:.2f} days to closest deadline)")

# Load submissions into a DataFrame
df = pd.DataFrame(data['submissions'])

# Convert submission times to datetime (UTC-aware)
df['first_submission_time'] = pd.to_datetime(df['first_submission_time'], utc=True)

# Compute hours_before_close for all submissions
df['hours_before_close'] = (df['shuttle_id'].map(shuttle_deadlines) - df['first_submission_time']).dt.total_seconds() / 3600
# Avoid zero values for log scale
df['hours_before_close'] = df['hours_before_close'].clip(lower=1)

# Compute days_before_close for linear plotting
df['days_before_close'] = df['hours_before_close'] / 24

# Sort by shuttle and days before close
df.sort_values(by=['shuttle_id', 'days_before_close'], ascending=[True, False], inplace=True)

# Calculate cumulative number of projects per shuttle
df['cumulative_projects'] = df.groupby('shuttle_id').cumcount() + 1

# Calculate cumulative tile utilisation as a percentage
df['cumulative_tiles'] = df.groupby('shuttle_id')['tile_count'].cumsum()
df['tile_utilisation_pct'] = 100 * df['cumulative_tiles'] / df['shuttle_id'].map(shuttle_tiles_total)

# Choose x-axis column based on log_x
x_col = 'hours_before_close' if log_x else 'days_before_close'
xlabel = 'Hours Before Tapeout' if log_x else 'Days Before Tapeout'

# Plot the projects graph
plt.figure(figsize=(10, 6))
for shuttle_id, group in df.groupby('shuttle_id'):
    shuttle_name = id_to_name.get(shuttle_id, f"Shuttle {shuttle_id}")
    if shuttle_name in skip_shuttles:
        continue

    print(f"shuttle {shuttle_name} [{shuttle_id}] : {group['cumulative_projects'].values[-1]}")

    linestyle = 'dotted'
    alpha = 0.35
    if shuttle_id == closest_shuttle_id:
        linestyle = 'solid'
        alpha = 1

    plt.plot(
        group[x_col].values,
        group['cumulative_projects'].values,
        label=f"Shuttle {shuttle_name}",
        alpha=alpha
    )

plt.gca().invert_xaxis()
if log_x:
    plt.xscale('log')

update_date = datetime.now().strftime("%d %B")
plt.xlabel(xlabel)
plt.ylabel('Number of Projects')
plt.title(f'Tiny Tapeout projects submitted over time - updated {update_date}')
plt.legend(loc="upper left")
plt.grid(True)
plt.savefig("tt_projects.png")

# Plot tile utilisation graph
plt.figure(figsize=(10, 6))
for shuttle_id, group in df.groupby('shuttle_id'):
    shuttle_name = id_to_name.get(shuttle_id, f"Shuttle {shuttle_id}")
    if shuttle_name in skip_shuttles:
        continue

    alpha = 1 if shuttle_id == closest_shuttle_id else 0.35

    plt.plot(
        group[x_col].values,
        group['tile_utilisation_pct'].values,
        label=shuttle_name,
        alpha=alpha
    )

plt.gca().invert_xaxis()
if log_x:
    plt.xscale('log')

plt.xlabel(xlabel)
plt.ylabel('Tile Utilisation (%)')
plt.title(f'Tiny Tapeout tile utilisation - updated {update_date}')
plt.legend(loc="upper left")
plt.grid(True)
plt.savefig("tt_utilisation.png")

if args.show:
    plt.show()
