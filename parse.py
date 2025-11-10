import requests
import json
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt

log_x = True

# Fetch JSON data from the API
url = "https://app.tinytapeout.com/api/shuttles/submission-stats"
response = requests.get(url)
response.raise_for_status()  # Raise an error if request failed
data = response.json()

# Optionally, save it locally for later use
with open("data.json", "w") as file:
    json.dump(data, file, indent=4)

# Extract shuttle info
shuttles = data['shuttles']
id_to_name = {item["id"]: item["name"] for item in shuttles}
shuttle_deadlines = {item["id"]: pd.to_datetime(item["deadline"]) for item in shuttles}

# Load submissions into a DataFrame
df = pd.DataFrame(data['submissions'])

# Convert submission times to datetime (UTC-aware)
df['first_submission_time'] = pd.to_datetime(df['first_submission_time'], format='ISO8601')

# Calculate days before shuttle closed
for shuttle_id, deadline in shuttle_deadlines.items():
    df.loc[df['shuttle_id'] == shuttle_id, 'days_before_close'] = (
        (deadline - df.loc[df['shuttle_id'] == shuttle_id, 'first_submission_time']).dt.total_seconds() / (24*3600)
    ).astype(int) + 1

# Sort by shuttle and days before close
df.sort_values(by=['shuttle_id', 'days_before_close'], ascending=[True, False], inplace=True)

# Calculate cumulative number of projects per shuttle
df['cumulative_projects'] = df.groupby('shuttle_id').cumcount() + 1

# Plot the graph
plt.figure(figsize=(10, 6))
skip_names = [
    "Tiny Tapeout 4", "Tiny Tapeout 10", "Tiny Tapeout CAD 25a",
    "Tiny Tapeout IHP 0p2", "Tiny Tapeout IHP 0p3",
    "Tiny Tapeout IHP 25a", "Tiny Tapeout Sky 25a", "Tiny Tapeout GF 0p2"
]

for shuttle_id, group in df.groupby('shuttle_id'):
    shuttle_name = id_to_name.get(shuttle_id, f"Shuttle {shuttle_id}")
    print(shuttle_name)
    if shuttle_name in skip_names:
        print(f'skipping {shuttle_name}')
        continue

    print(f"shuttle {shuttle_name} : {group['cumulative_projects'].values[-1]}")

    linestyle = 'dotted'
    alpha = 0.35
    if shuttle_name == "Tiny Tapeout SKY 25b":
        linestyle = 'solid'
        alpha = 1

    plt.plot(
        group['days_before_close'].values,
        group['cumulative_projects'].values,
        label=f"Shuttle {shuttle_name}",
        alpha=alpha
    )

plt.gca().invert_xaxis()
if log_x:
    plt.xscale('log')

update_date = datetime.now().strftime("%d %B")
plt.xlabel('Days Before Tapeout')
plt.ylabel('Number of Projects')
plt.title(f'Tiny Tapeout shuttle utilisation - updated {update_date}')
plt.legend(loc="upper left")
plt.grid(True)
plt.savefig("tt_shuttles.png")
plt.show()
