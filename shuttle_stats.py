import requests
import argparse
import json
import numpy as np
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

# Plot total projects per year (all shuttles)
shuttle_year = {item["id"]: pd.to_datetime(item["deadline"]).year for item in shuttles}
projects_per_shuttle = df.groupby('shuttle_id')['cumulative_projects'].max()
year_totals = {}
for shuttle_id, count in projects_per_shuttle.items():
    year = shuttle_year.get(shuttle_id)
    if year:
        year_totals[year] = year_totals.get(year, 0) + count

# TT brand colours
tt_blue      = '#040371'
tt_hot_pink  = '#f82381'
tt_cyan      = '#3dfef7'
tt_yellow    = '#fef244'

# Average projects per completed production shuttle (exclude experimental 0p slugs)
slug_map = {item["id"]: item["slug"] for item in shuttles}
past_shuttle_ids = {item["id"] for item in shuttles if pd.to_datetime(item["deadline"]) < now_utc}
production_past_ids = {sid for sid in past_shuttle_ids if '0p' not in slug_map.get(sid, '')}
production_projects = [cnt for sid, cnt in projects_per_shuttle.items() if sid in production_past_ids]
avg_per_shuttle = sum(production_projects) / len(production_projects) if production_projects else 0
print(f"Avg projects per production shuttle: {avg_per_shuttle:.1f} (over {len(production_projects)} shuttles)")

# 2026: actual from data + 5 more shuttles estimated
actual_2026 = year_totals.get(2026, 0)
estimated_2026_extra = 5 * avg_per_shuttle

# Shuttle counts per year
shuttles_per_year_actual = {}
for sid, yr in shuttle_year.items():
    shuttles_per_year_actual[yr] = shuttles_per_year_actual.get(yr, 0) + 1
shuttles_in_2026 = shuttles_per_year_actual.get(2026, 0)
total_2026_shuttles = shuttles_in_2026 + 5

# Extrapolate 2027 shuttle count using quadratic fit (normalize years to avoid float instability)
fit_years = sorted(shuttles_per_year_actual.keys())
fit_counts = [total_2026_shuttles if y == 2026 else shuttles_per_year_actual[y] for y in fit_years]
base_year = fit_years[0]
fit_years_norm = [y - base_year for y in fit_years]
coeffs = np.polyfit(fit_years_norm, fit_counts, 2)
estimated_2027_shuttles = max(total_2026_shuttles, int(round(np.polyval(coeffs, 2027 - base_year))))
estimated_2027 = estimated_2027_shuttles * avg_per_shuttle
print(f"2026 shuttles in data: {shuttles_in_2026}, total projected: {total_2026_shuttles}")
print(f"2027 shuttles extrapolated: {estimated_2027_shuttles}")
print(f"Estimated 2026 extra: {estimated_2026_extra:.0f}, Estimated 2027 total: {estimated_2027:.0f}")

past_years = sorted(y for y in year_totals if y < 2026)

# Shuttle line: actual through 2026, then dashed to 2027 — share 2026 point so no gap
line_actual_x = [str(y) for y in past_years] + ['2026']
line_actual_y = [shuttles_per_year_actual.get(y, 0) for y in past_years] + [total_2026_shuttles]
line_est_x = ['2026', '2027']
line_est_y = [total_2026_shuttles, estimated_2027_shuttles]

def make_chart(filename, bar_actual_color, bar_est_color):
    fig, ax1 = plt.subplots(figsize=(10, 6))
    fig.patch.set_facecolor('white')

    ax1.bar([str(y) for y in past_years], [year_totals[y] for y in past_years],
            color=bar_actual_color, label='Projects (actual)')
    ax1.bar('2026', actual_2026, color=bar_actual_color)
    ax1.bar('2026', estimated_2026_extra, bottom=actual_2026,
            color=bar_est_color, label='Projects (estimated)')
    ax1.bar('2027', estimated_2027, color=bar_est_color)
    ax1.set_xlabel('Year')
    ax1.set_ylabel('Number of Projects')

    ax2 = ax1.twinx()
    ax2.plot(line_actual_x, line_actual_y,
             color='black', marker='o', linewidth=2.5, markersize=7,
             label='Shuttles (actual)')
    ax2.plot(line_est_x, line_est_y,
             color='black', marker='o', linewidth=2.5, markersize=7,
             linestyle='dashed', label='Shuttles (estimated)')
    ax2.set_ylabel('Number of Shuttles')
    ax2.set_ylim(bottom=0)

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', handlelength=3)

    plt.title(f'Tiny Tapeout total projects taped out per year - updated {update_date}')
    ax1.grid(True, axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(filename)
    if args.show:
        plt.show()
    plt.close()

make_chart("tt_projects_per_year.png", '#8486b8', '#888888')
