import sqlite3
import matplotlib.pyplot as plt
import os

# Output folder
out_dir = 'static/analysis'
os.makedirs(out_dir, exist_ok=True)

# Connect to database
conn = sqlite3.connect('instance/fuel.db')
cur = conn.cursor()

# PIE CHART: Fuel type distribution
cur.execute("SELECT fuel FROM predictions JOIN users ON users.id = predictions.user_id")
fuel_data = [row[0] for row in cur.fetchall()]
if fuel_data:
    labels = list(set(fuel_data))
    sizes = [fuel_data.count(label) for label in labels]
    plt.figure()
    plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140)
    plt.title("Fuel Type Usage")
    plt.savefig(f"{out_dir}/pie_chart.png")
    plt.close()

# BAR GRAPH: CO2 ratings
cur.execute("SELECT result FROM predictions")
co2_values = []
for row in cur.fetchall():
    try:
        val = float(row[0].split()[-1])
        co2_values.append(round(val))
    except:
        continue
if co2_values:
    from collections import Counter
    counts = Counter(co2_values)
    plt.figure()
    plt.bar(counts.keys(), counts.values(), color='skyblue')
    plt.title("CO₂ Ratings Distribution")
    plt.xlabel("CO₂ Rating (L/100 km)")
    plt.ylabel("Frequency")
    plt.savefig(f"{out_dir}/bar_graph.png")
    plt.close()

# LINE GRAPH: Just showing index vs. result as time series
if co2_values:
    plt.figure()
    plt.plot(co2_values, marker='o', linestyle='-', color='green')
    plt.title("Fuel Efficiency Over Time")
    plt.xlabel("Prediction #")
    plt.ylabel("L/100 km")
    plt.savefig(f"{out_dir}/line_graph.png")
    plt.close()

# HISTOGRAM: Engine Size — replace with actual field if needed
cur.execute("SELECT engine FROM predictions JOIN users ON users.id = predictions.user_id")
engines = [int(row[0]) for row in cur.fetchall() if row[0].isdigit()]
if engines:
    plt.figure()
    plt.hist(engines, bins=7, color='purple', edgecolor='black')
    plt.title("Engine Size Distribution")
    plt.xlabel("Engine Size")
    plt.ylabel("Count")
    plt.savefig(f"{out_dir}/histogram.png")
    plt.close()

conn.close()
