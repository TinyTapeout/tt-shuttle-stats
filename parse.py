import pandas as pd
from datetime import datetime
import json
import matplotlib.pyplot as plt

# Read data from CSV file
df = pd.read_csv('data.csv')

log_x = True

# Read shuttle info
with open("shuttles.json", "r") as file:
    shuttle_info = json.load(file)
    id_to_name = {item["id"]: item["name"] for item in shuttle_info}

# Add deadlines for each shuttle
shuttle_deadlines = {4: "2023-09-08", 5: "2023-11-04", 6: "2024-04-19", 7: "2024-06-01", 8: "2024-09-06", 9: "2024-11-10", 10: "2025-03-10", 1002: "2025-09-01", 400: "2025-09-15"}

# Convert deadlines to datetime objects
for shuttle_id, deadline in shuttle_deadlines.items():
#    print(f"shuttle {shuttle_id}, deadline {deadline}");
    shuttle_deadlines[shuttle_id] = pd.Timestamp(deadline)

# Convert first_submission_time to datetime objects
df['first_submission_time'] = pd.to_datetime(df['first_submission_time']).dt.tz_localize(None)

# Calculate days before shuttle closed
for shuttle_id, deadline in shuttle_deadlines.items():
    df.loc[df['shuttle_id'] == shuttle_id, 'days_before_close'] = (deadline - df.loc[df['shuttle_id'] == shuttle_id, 'first_submission_time']).dt.days + 1

# Sort the DataFrame by shuttle ID and days before close
#df.sort_values(by=['shuttle_id', 'days_before_close'], inplace=True)
df.sort_values(by=['shuttle_id', 'days_before_close'], ascending=[True, False], inplace=True)

# Calculate cumulative sum of projects for each shuttle
df['cumulative_projects'] = df.groupby('shuttle_id').cumcount() + 1

# Plot the graph
plt.figure(figsize=(10, 6))
for shuttle_id, group in df.groupby('shuttle_id'):
    shuttle_name = id_to_name[shuttle_id]
    if shuttle_name in ["Tiny Tapeout 10", "Tiny Tapeout CAD 25a", "Tiny Tapeout IHP 0p2", "Tiny Tapeout IHP 0p3", "Tiny Tapeout IHP 25a", "Tiny Tapeout Sky 25a"] :
        continue
    print(f"shuttle {shuttle_name} : {group['cumulative_projects'].values[-1]}")
    linestyle = 'dotted'
    alpha = 0.35
    if shuttle_name == "Tiny Tapeout SKY 25a":
        linestyle = 'solid'
        alpha = 1
    plt.plot(group['days_before_close'].values, group['cumulative_projects'].values, label=f"Shuttle {shuttle_name}", alpha=alpha) #linestyle=linestyle)
plt.gca().invert_xaxis()

if logx:
    plt.xscale('log')

update_date = datetime.now().strftime("%d %B")
plt.xlabel('Days Before Tapeout')
plt.ylabel('Number of Projects')
plt.title(f'Tiny Tapeout shuttle utilisation - updated {update_date}')
plt.legend(loc="upper left")
plt.grid(True)
plt.savefig("tt_shuttles.png")
