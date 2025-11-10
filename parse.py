import pandas as pd
from datetime import datetime
import json
import matplotlib.pyplot as plt

log_x = False

# Load all data from the single JSON file
with open("data.json", "r") as file:
    data = json.load(file)

# Extract shuttle info
shuttles = data['shuttles']
id_to_name = {item["id"]: item["name"] for item in shuttles}
shuttle_deadlines = {item["id"]: pd.Timestamp(item["deadline"]) for item in shuttles}

# Load submissions into a DataFrame
df = pd.DataFrame(data['submissions'])

# Convert first_submission_time to datetime objects
df['first_submission_time'] = pd.to_datetime(df['first_submission_time']).dt.tz_localize(None)

# Calculate days before shuttle closed
for shuttle_id, deadline in shuttle_deadlines.items():
    df.loc[df['shuttle_id'] == shuttle_id, 'days_before_close'] = (
        deadline - df.loc[df['shuttle_id'] == shuttle_id, 'first_submission_time']
    ).dt.days + 1

# Sort the DataFrame by shuttle ID and days before close
df.sort_values(by=['shuttle_id', 'days_before_close'], ascending=[True, False], inplace=True)

# Calculate cumulative sum of projects for each shuttle
df['cumulative_projects'] = df.groupby('shuttle_id').cumcount() + 1

# Plot the graph
plt.figure(figsize=(10, 6))
for shuttle_id, group in df.groupby('shuttle_id'):
    shuttle_name = id_to_name.get(shuttle_id, f"Shuttle {shuttle_id}")
    
    # Skip certain shuttles
    skip_names = [
        "Tiny Tapeout 4", "Tiny Tapeout 10", "Tiny Tapeout CAD 25a",
        "Tiny Tapeout IHP 0p2", "Tiny Tapeout IHP 0p3",
        "Tiny Tapeout IHP 25a", "Tiny Tapeout Sky 25a", "Tiny Tapeout GF 0p2"
    ]
    if shuttle_name in skip_names:
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
