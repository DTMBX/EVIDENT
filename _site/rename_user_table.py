"""
Rename user table to users (to match SQLAlchemy model)
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'instance', 'barberx.db')

def rename_table():
    print("\n" + "="*80)
    print("Renaming 'user' table to 'users'")
    print("="*80 + "\n")
    
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found at: {DB_PATH}")
        return False
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check current tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [t[0] for t in cursor.fetchall()]
        
        print(f"Current tables: {', '.join(tables)}")
        
        if 'users' in tables:
            print("✅ Table 'users' already exists")
            conn.close()
            return True
        
        if 'user' not in tables:
            print("❌ Table 'user' does not exist")
            conn.close()
            return False
        
        print("\nRenaming table...")
        cursor.execute("ALTER TABLE user RENAME TO users")
        conn.commit()
        
        print("✅ Table renamed successfully")
        
        # Verify
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [t[0] for t in cursor.fetchall()]
        print(f"\nNew tables: {', '.join(tables)}")
        
        # Show users
        cursor.execute("SELECT email, role, subscription_tier FROM users")
        users = cursor.fetchall()
        
        if users:
            print(f"\nUsers ({len(users)}):")
            for email, role, tier in users:
                print(f"  • {email:30} | role={role or 'user':10} | tier={tier}")
        
        conn.close()
        
        print("\n" + "="*80)
        print("Migration Complete!")
        print("="*80 + "\n")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
        conn.close()
        return False

if __name__ == '__main__':
    rename_table()
