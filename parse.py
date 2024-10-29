import pandas as pd
import matplotlib.pyplot as plt

# Read data from CSV file
df = pd.read_csv('data.csv')

# Add deadlines for each shuttle
shuttle_deadlines = {4: "2023-09-08", 5: "2023-11-04", 6: "2024-04-19", 7: "2024-06-01", 8: "2024-09-06", 9: "2024-11-10"}

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
    if shuttle_id == 1000:
        continue
    print(f"shuttle {shuttle_id} : {group['cumulative_projects'].values[-1]}")
    linestyle = 'dotted'
    alpha = 0.35
    if shuttle_id == 9:
        linestyle = 'solid'
        alpha = 1
    plt.plot(group['days_before_close'].values, group['cumulative_projects'].values, label=f"Shuttle {shuttle_id}", alpha=alpha) #linestyle=linestyle)
plt.gca().invert_xaxis()
#plt.xscale('log')
#plt.yscale('log')
plt.xlabel('Days Before Close')
plt.ylabel('Number of Projects')
plt.title('Tiny Tapeout shuttles')
plt.legend()
plt.grid(True)
plt.savefig("tt_shuttles.png")
