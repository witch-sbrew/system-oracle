import sqlite3

conn = sqlite3.connect("telemetry_history.db")
cursor = conn.cursor()

# Get the last 10 entries
cursor.execute(
    "SELECT timestamp, name, pid FROM activity ORDER BY timestamp DESC LIMIT 10"
)
rows = cursor.fetchall()

print(f"{'Timestamp':<25} | {'Process Name':<20} | {'PID'}")
print("-" * 60)
for row in rows:
    print(f"{row[0]:<25} | {row[1]:<20} | {row[2]}")

# Show total count
cursor.execute("SELECT COUNT(*) FROM activity")
print(f"\nTotal records in database: {cursor.fetchone()[0]}")

conn.close()
