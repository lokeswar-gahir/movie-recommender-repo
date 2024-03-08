import pymysql
from werkzeug.security import generate_password_hash

connection = pymysql.connect(host="localhost", user="root", password="root")
cursor = connection.cursor()

hashed_password = generate_password_hash("Admin")
# Executing SQL query
cursor.execute("DROP DATABASE IF EXISTS auth_db;")
cursor.execute("CREATE DATABASE IF NOT EXISTS auth_db;")
cursor.execute("USE auth_db;")
cursor.execute("CREATE TABLE users (id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, username VARCHAR(50) NOT NULL UNIQUE, email VARCHAR(255) NOT NULL UNIQUE, hashed_password VARCHAR(255) NOT NULL, password VARCHAR(255) NOT NULL);")
cursor.execute(f"INSERT INTO users (username, email, hashed_password, password) VALUES ('Admin', 'Admin@Admin.com', '{hashed_password}', 'Admin');")
cursor.execute("SELECT * FROM users;")
for user in cursor.fetchall():
    print(user)
connection.commit()
cursor.close()
connection.close()