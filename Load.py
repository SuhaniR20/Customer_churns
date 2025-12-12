import mysql.connector as sc
import pandas as pd
import os
import shutil
import glob

# ---------------------- FOLDERS ----------------------
raw_folder = r'PROJECT\DATA\Raw_unprocessed_data'             # RAW folder
processed_folder = r'PROJECT\DATA\Processed_data'  # PROCESSED folder

# ---------------------- DB CONNECTION ----------------------
def db_connection():
    conn = sc.connect(
        host='localhost',
        user='root',
        password='Root@1234',
        database='suhani_test',
        port=3306
    )
    cursor = conn.cursor()
    return cursor, conn

# ---------------------- ALTER PHONE COLUMN ----------------------
def alter_phone_column(table_name):
    cursor, conn = db_connection()
    try:
        q = f"ALTER TABLE {table_name} MODIFY COLUMN phone VARCHAR(50)"
        cursor.execute(q)
        conn.commit()
    except:
        pass
    cursor.close()
    conn.close()

# ---------------------- LOAD FILE FUNCTION ----------------------
def load_files(table_name, file_path):
    if os.path.exists(file_path):
        cursor, conn = db_connection()
        alter_phone_column(table_name)

        # Delete old records
        sql = f"DELETE FROM {table_name} WHERE file_name = %s"
        cursor.execute(sql, (file_path,))
        conn.commit()

        # Read file
        if file_path.endswith(".csv"):
            df = pd.read_csv(file_path)
        elif file_path.endswith(".txt"):
            df = pd.read_csv(file_path, delimiter="|")
        elif file_path.endswith(".json"):
            df = pd.read_json(file_path)
        elif file_path.endswith(".xlsx"):
            df = pd.read_excel(file_path)
        else:
            print(f"Unsupported format: {file_path}")
            return

        # Add columns
        df["file_name"] = file_path
        df["user_name"] = "suhani_test"
        df["rownumber"] = range(1, len(df) + 1)

        # SQL Insert
        column_names = df.columns.tolist()
        columns_str = ", ".join(f"`{col}`" for col in column_names)
        placeholders = ", ".join(["%s"] * len(column_names))
        insert_sql = f"INSERT IGNORE INTO {table_name} ({columns_str}) VALUES ({placeholders})"
        records = [tuple(row) for row in df.values.tolist()]
        cursor.executemany(insert_sql, records)

        # Update timestamp
        update_sql = f"UPDATE {table_name} SET Last_updated_at = CURRENT_TIMESTAMP() WHERE file_name = %s"
        cursor.execute(update_sql, (file_path,))
        conn.commit()

        print(f"Loaded into {table_name}: {file_path}")

        # Copy to processed folder
        shutil.copy(file_path, processed_folder)
        print("Copied to processed folder!")

        # Delete original file
        os.remove(file_path)
        print("Deleted from RAW folder!")

        cursor.close()
        conn.close()
    else:
        print(f"File not found: {file_path}")

# ---------------------- AUTO LIST RAW FILES ----------------------
all_files = glob.glob(raw_folder + "/*")  # List all files in RAW folder

# ---------------------- TABLE MAPPING BASED ON FILE NAME ----------------------
table_mapping = {
    "orders": "ecommerce_orders_raw_table",
    "crm": "crm_customer_raw_table",
    "marketing": "marketing_events_raw_table",
    "support": "support_tickets_raw_table"
}



for file_path in all_files:
    file_lower = os.path.basename(file_path).lower()
    target_table = None

    # Match based on filename keywords
    for key, table in table_mapping.items():
        if key in file_lower:
            target_table = table
            break

    # Load into the chosen table
    if target_table:
        load_files(target_table, file_path)
        print(f"File {file_path} loaded into {target_table}")
    else:
        print(f"No table mapping found for: {file_path}")