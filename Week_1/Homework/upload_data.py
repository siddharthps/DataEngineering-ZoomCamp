import os
import gzip
import shutil
import pandas as pd
import psycopg2
from sqlalchemy import create_engine
import argparse
import requests

def download_data(url, file_name):
    print(f"Downloading {file_name} ...")
    r = requests.get(url, stream=True)
    r.raise_for_status()
    with open(file_name, 'wb') as f:
        shutil.copyfileobj(r.raw, f)
    print("Download completed.")

def read_csv_file(file_name):
    """Read CSV file depending on its format."""
    if file_name.endswith('.gz'):
        with gzip.open(file_name, 'rt') as f:
            return pd.read_csv(f)
    else:
        return pd.read_csv(file_name)

def create_postgres_connection(user, password, host, port, dbname):
    """Create a PostgreSQL connection."""
    conn = psycopg2.connect(
        dbname=dbname, user=user, password=password, host=host, port=port
    )
    return conn

def upload_to_postgres(df, conn, table_name):
    """Upload DataFrame to PostgreSQL table."""
    print(f"Uploading data to {table_name} table...")
    engine = create_engine(f'postgresql://{conn.info.user}:{conn.info.password}@{conn.info.host}:{conn.info.port}/{conn.info.dbname}')
    df.to_sql(table_name, engine, index=False, if_exists='replace')  # Change if_exists to 'append' if you don't want to replace
    print(f"Data uploaded to {table_name} table.")

def main(args):
    # Download the data
    file_name = args.url.split('/')[-1]
    download_data(args.url, file_name)
    
    # Read the CSV file
    df = read_csv_file(file_name)
    
    # Connect to the PostgreSQL database
    conn = create_postgres_connection(args.user, args.password, args.host, args.port, args.db)
    
    # Upload data to PostgreSQL
    upload_to_postgres(df, conn, args.table)
    
    # Close the connection
    conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upload data to PostgreSQL")
    parser.add_argument('--user', type=str, required=True, help="PostgreSQL user")
    parser.add_argument('--password', type=str, required=True, help="PostgreSQL password")
    parser.add_argument('--host', type=str, required=True, help="PostgreSQL host")
    parser.add_argument('--port', type=int, required=True, help="PostgreSQL port")
    parser.add_argument('--db', type=str, required=True, help="PostgreSQL database")
    parser.add_argument('--table', type=str, required=True, help="PostgreSQL table")
    parser.add_argument('--url', type=str, required=True, help="URL to download the CSV file")

    args = parser.parse_args()
    main(args)
