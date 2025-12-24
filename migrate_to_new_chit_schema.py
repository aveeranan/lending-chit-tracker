"""
Migrate database from old chit schema to new chit schema.

This script:
1. Backs up old chit data
2. Drops old tables
3. Creates new tables
4. Migrates data where possible (WARNING: old adjustments cannot be migrated)
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'database', 'lending.db')

print("=" * 70)
print("CHIT SCHEMA MIGRATION")
print("=" * 70)
print()
print("⚠️  WARNING: This will delete all existing chit data!")
print("   Old chit adjustments CANNOT be migrated to the new structure.")
print("   The new schema uses a completely different business logic.")
print()

response = input("Do you want to proceed? (type 'yes' to continue): ")
if response.lower() != 'yes':
    print("Migration cancelled.")
    exit(0)

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

print("\n" + "=" * 70)
print("Step 1: Backing up old chit data")
print("=" * 70)

# Check if old tables exist
cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'chit%'")
old_tables = [row['name'] for row in cursor.fetchall()]

print(f"Found old chit tables: {old_tables}")

if old_tables:
    backup_file = f"chit_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
    print(f"\nBacking up to: {backup_file}")

    with open(backup_file, 'w') as f:
        for table in old_tables:
            cursor = conn.execute(f"SELECT sql FROM sqlite_master WHERE name='{table}'")
            create_sql = cursor.fetchone()
            if create_sql:
                f.write(f"{create_sql[0]};\n\n")

            cursor = conn.execute(f"SELECT * FROM {table}")
            rows = cursor.fetchall()
            if rows:
                columns = [description[0] for description in cursor.description]
                for row in rows:
                    values = ', '.join([f"'{str(v).replace("'", "''")}'" if v is not None else 'NULL' for v in row])
                    f.write(f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({values});\n")
                f.write("\n")

    print(f"✓ Backup saved to {backup_file}")

print("\n" + "=" * 70)
print("Step 2: Dropping old chit tables")
print("=" * 70)

# Drop old tables in correct order (reverse foreign key dependencies)
drop_order = [
    'chit_adjustments',
    'chit_monthly_schedule',
    'chits'
]

for table in drop_order:
    try:
        conn.execute(f"DROP TABLE IF EXISTS {table}")
        print(f"✓ Dropped table: {table}")
    except Exception as e:
        print(f"✗ Error dropping {table}: {e}")

# Drop old indexes
old_indexes = [
    'idx_chits_borrower',
    'idx_chits_status',
    'idx_chit_schedule_chit',
    'idx_chit_adjustments_schedule',
    'idx_chit_adjustments_loan'
]

for idx in old_indexes:
    try:
        conn.execute(f"DROP INDEX IF EXISTS {idx}")
        print(f"✓ Dropped index: {idx}")
    except Exception as e:
        print(f"✗ Error dropping {idx}: {e}")

conn.commit()

print("\n" + "=" * 70)
print("Step 3: Creating new chit tables")
print("=" * 70)

# Read and execute new schema
schema_path = os.path.join(os.path.dirname(__file__), 'database', 'schema.sql')

print(f"Reading schema from: {schema_path}")

with open(schema_path, 'r') as f:
    schema_sql = f.read()

try:
    conn.executescript(schema_sql)
    print("✓ New chit schema created successfully")
except Exception as e:
    print(f"✗ Error creating schema: {e}")
    conn.close()
    exit(1)

conn.commit()

print("\n" + "=" * 70)
print("Step 4: Verifying new tables")
print("=" * 70)

cursor = conn.execute("""
    SELECT name FROM sqlite_master
    WHERE type='table' AND name IN (
        'chit_groups', 'borrower_chit_links', 'adjustments', 'direct_chit_payments'
    )
    ORDER BY name
""")

new_tables = [row['name'] for row in cursor.fetchall()]
expected_tables = ['adjustments', 'borrower_chit_links', 'chit_groups', 'direct_chit_payments']

print(f"Created tables: {new_tables}")

if set(new_tables) == set(expected_tables):
    print("✓ All new tables created successfully")
else:
    missing = set(expected_tables) - set(new_tables)
    print(f"✗ Missing tables: {missing}")

conn.close()

print("\n" + "=" * 70)
print("MIGRATION COMPLETE")
print("=" * 70)
print()
print("Next steps:")
print("1. Use the UI to create chit groups")
print("2. Link borrowers to their chits")
print("3. Start making adjustments using the new flow")
print()
print("Note: Old chit data has been backed up but NOT migrated.")
print(f"      Backup file: {backup_file if 'backup_file' in locals() else 'N/A'}")
print()
