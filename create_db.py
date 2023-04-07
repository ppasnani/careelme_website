import mysql.connector

mydb = mysql.connector.connect(
	host="localhost",
	user="root",
	passwd="password123",
	#database="careelme_jobs"
	)

my_cursor = mydb.cursor()

# Commented below out that actually creates the database to avoid overwriting the existing db
# my_cursor.execute("CREATE DATABASE careelme_jobs")

# # Delete the database using below
# # Execute the DROP DATABASE command to delete the database
# my_cursor.execute("DROP DATABASE careelme_jobs")

# # Commit the transaction
# mydb.commit()

# # Close the cursor and database connection
# my_cursor.close()
# mydb.close()

my_cursor.execute("SHOW DATABASES")
for db in my_cursor:
	print (db)

