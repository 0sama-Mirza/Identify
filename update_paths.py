import sqlite3

# Path to your SQLite database
db_path = 'database.db'  # Replace with your actual database file path

# Establish a connection to the SQLite database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Define the SQL query
query = """
    SELECT id,
           SUBSTR(image_path, INSTR(image_path, 'original_images/') + LENGTH('original_images/')) AS updated_image_path
    FROM event_images
    WHERE image_path LIKE '/home/archmax/startup/Evently/uploads/event%/original_images/%';
"""

# Execute the query
cursor.execute(query)

# Fetch all the results
rows = cursor.fetchall()

# Print the results
for row in rows:
    print(f"ID: {row[0]}, Updated Image Path: {row[1]}")

# Close the database connection
conn.close()
