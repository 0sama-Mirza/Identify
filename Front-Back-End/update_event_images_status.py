import sqlite3

# Path to your SQLite database
db_path = 'database.db'  # Adjust path if needed

# Connect to the SQLite database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# --- Check if 'status' column already exists ---
cursor.execute("PRAGMA table_info(event_images);")
columns = [col[1] for col in cursor.fetchall()]

if 'status' not in columns:
    print("Adding 'status' column to 'event_images' table...")

    # Add the 'status' column
    cursor.execute("""
        ALTER TABLE event_images 
        ADD COLUMN status TEXT DEFAULT 'unsorted'
    """)
    conn.commit()

    print("Column 'status' added successfully.")

else:
    print("'status' column already exists. No changes made.")

# --- Optional: print updated schema ---
cursor.execute("PRAGMA table_info(event_images);")
print("\nUpdated schema for 'event_images':")
for col in cursor.fetchall():
    print(col)

# Close the connection
conn.close()
