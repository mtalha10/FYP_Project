# File: Authentication/userdb.py
import sqlite3
import bcrypt
import re
from datetime import datetime


class DatabaseOperations:
    @staticmethod
    def init_db():
        """Initialize the database and create the users table if it doesn't exist."""
        conn = sqlite3.connect('app.db')
        c = conn.cursor()

        # Check if the 'users' table exists
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        table_exists = c.fetchone() is not None

        if not table_exists:
            # Create the table with all necessary columns
            c.execute('''
                CREATE TABLE users (
                    username TEXT PRIMARY KEY, 
                    password TEXT NOT NULL, 
                    email TEXT NOT NULL, 
                    role TEXT DEFAULT 'user',
                    full_name TEXT DEFAULT '',
                    bio TEXT DEFAULT '',
                    profile_picture TEXT DEFAULT NULL,
                    created_at TEXT NOT NULL
                )
            ''')
        else:
            # If table exists, add any missing columns
            c.execute("PRAGMA table_info(users)")
            columns = [column[1] for column in c.fetchall()]

            if 'full_name' not in columns:
                c.execute("ALTER TABLE users ADD COLUMN full_name TEXT DEFAULT ''")
            if 'bio' not in columns:
                c.execute("ALTER TABLE users ADD COLUMN bio TEXT DEFAULT ''")
            if 'profile_picture' not in columns:
                c.execute("ALTER TABLE users ADD COLUMN profile_picture TEXT DEFAULT NULL")
            if 'created_at' not in columns:
                c.execute("ALTER TABLE users ADD COLUMN created_at TEXT NOT NULL DEFAULT ''")

        conn.commit()
        conn.close()

    @staticmethod
    def add_user(username, password, email, role="user"):
        """Add a new user to the database."""
        if not username or not password or not email:
            return False, "All fields are required."
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            return False, "Invalid email format."
        if len(password) < 8:
            return False, "Password must be at least 8 characters long."

        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        conn = sqlite3.connect('app.db')
        c = conn.cursor()
        try:
            created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c.execute("""
                INSERT INTO users (username, password, email, role, full_name, bio, created_at) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (username, hashed.decode('utf-8'), email, role, '', '', created_at))
            conn.commit()
            return True, "Account created successfully!"
        except sqlite3.IntegrityError:
            return False, "Username already exists."
        finally:
            conn.close()

    @staticmethod
    def verify_user(username, password):
        """Verify the user's credentials."""
        conn = sqlite3.connect('app.db')
        c = conn.cursor()
        c.execute("SELECT password FROM users WHERE username=?", (username,))
        result = c.fetchone()
        conn.close()
        if result:
            return bcrypt.checkpw(password.encode('utf-8'),
                                  result[0].encode('utf-8'))
        return False

    @staticmethod
    def get_user_profile(username):
        """Retrieve the user's profile data."""
        conn = sqlite3.connect('app.db')
        c = conn.cursor()
        try:
            c.execute("""
                SELECT username, email, role, full_name, bio, profile_picture, created_at 
                FROM users WHERE username=?
            """, (username,))
            result = c.fetchone()

            if result:
                return {
                    'username': result[0],
                    'email': result[1],
                    'role': result[2],
                    'full_name': result[3] or '',
                    'bio': result[4] or '',
                    'profile_picture': result[5],
                    'created_at': result[6]
                }
            return None
        finally:
            conn.close()

    @staticmethod
    def update_user_profile(username, updates):
        """Update the user's profile information."""
        allowed_fields = {'full_name', 'bio', 'profile_picture'}
        filtered_updates = {k: v for k, v in updates.items() if k in allowed_fields}

        if not filtered_updates:
            return False, "No valid fields to update"

        conn = sqlite3.connect('app.db')
        c = conn.cursor()
        try:
            # Build the SQL query dynamically based on the filtered updates
            query = "UPDATE users SET "
            params = []
            for key, value in filtered_updates.items():
                query += f"{key}=?, "
                params.append(value)
            query = query.rstrip(", ") + " WHERE username=?"
            params.append(username)

            c.execute(query, tuple(params))
            conn.commit()
            return True, "Profile updated successfully!"
        except Exception as e:
            return False, f"Error updating profile: {str(e)}"
        finally:
            conn.close()

    @staticmethod
    def change_user_password(username, current_password, new_password):
        """Change the user's password."""
        if not DatabaseOperations.verify_user(username, current_password):
            return False, "Invalid current password."

        if len(new_password) < 8:
            return False, "Password must be at least 8 characters long."

        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(new_password.encode('utf-8'), salt)
        conn = sqlite3.connect('app.db')
        c = conn.cursor()
        try:
            c.execute("UPDATE users SET password=? WHERE username=?",
                      (hashed.decode('utf-8'), username))
            conn.commit()
            return True, "Password changed successfully!"
        except Exception as e:
            return False, f"Error changing password: {str(e)}"
        finally:
            conn.close()

    @staticmethod
    def delete_user(username, password):
        """Delete a user from the database."""
        if not DatabaseOperations.verify_user(username, password):
            return False, "Invalid credentials."

        conn = sqlite3.connect('app.db')
        c = conn.cursor()
        try:
            c.execute("DELETE FROM users WHERE username=?", (username,))
            conn.commit()
            return True, "Account deleted successfully!"
        except Exception as e:
            return False, f"Error deleting account: {str(e)}"
        finally:
            conn.close()