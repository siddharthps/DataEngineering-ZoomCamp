import pandas as pd
import argparse
from sqlalchemy import create_engine
import requests
import gzip
import shutil

def main(params): 
    # Function that will be called by the pipeline script
    # Extract the input parameters
    user = params.user
    password = params.password
    host = params.host 
    port = params.port 
    db = params.db
    table_name = params.table_name
    url = params.url

    # Step 1: Download the CSV.GZ file using requests
    print("Downloading the compressed CSV file from the provided URL...")
    response = requests.get(url)
    if response.status_code == 200:
        # Save the downloaded .gz file locally
        with open('output.csv.gz', 'wb') as f_out:
            f_out.write(response.content)
        print("Download complete.")
    else:
        # Handle any download errors
        print(f"Error downloading the file: HTTP status code {response.status_code}")
        return

    # Step 2: Unzip the CSV file
    print("Unzipping the downloaded file...")
    with gzip.open('output.csv.gz', 'rb') as f_in:
        with open('output.csv', 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    print("Unzipping complete.")

    # Step 3: Connect to PostgreSQL database
    print("Connecting to the PostgreSQL database...")
    engine = create_engine(f'postgresql://{user}:{password}@{host}:{port}/{db}')

    # Step 4: Read the CSV file in chunks to handle large data
    print("Reading the unzipped CSV file in chunks...")
    df_iter = pd.read_csv('output.csv', iterator=True, chunksize=100000)

    # Step 5: Process the first chunk
    print("Processing the first chunk of data...")
    df = next(df_iter)
    df.tpep_pickup_datetime = pd.to_datetime(df.tpep_pickup_datetime)  # Convert pickup time to datetime format
    df.tpep_dropoff_datetime = pd.to_datetime(df.tpep_dropoff_datetime)  # Convert dropoff time to datetime format

    # Step 6: Insert the first chunk into the database
    print(f"Creating table '{table_name}' and inserting the first chunk...")
    df.head(n=0).to_sql(name=table_name, con=engine, if_exists='replace')  # Create the table schema
    df.to_sql(name=table_name, con=engine, if_exists='append')  # Insert the data

    # Step 7: Process and insert the remaining chunks
    print("Processing and inserting the remaining chunks...")
    while True:
        try:
            df = next(df_iter)  # Read the next chunk
            df.tpep_pickup_datetime = pd.to_datetime(df.tpep_pickup_datetime)  # Convert pickup time to datetime format
            df.tpep_dropoff_datetime = pd.to_datetime(df.tpep_dropoff_datetime)  # Convert dropoff time to datetime format
            df.to_sql(name=table_name, con=engine, if_exists='append')  # Insert the data into the database
            print("Inserted another chunk of data.")
        except StopIteration:
            # StopIteration is raised when there are no more chunks
            print("All data has been successfully inserted into the database.")
            break

if __name__ == '__main__':
    # Argument parser to parse the command-line arguments
    parser = argparse.ArgumentParser(description='Ingest CSV data to Postgres')
    parser.add_argument('--user', help='User name for PostgreSQL')
    parser.add_argument('--password', help='Password for PostgreSQL')
    parser.add_argument('--host', help='Host address for PostgreSQL')
    parser.add_argument('--port', help='Port number for PostgreSQL')
    parser.add_argument('--db', help='Database name in PostgreSQL')
    parser.add_argument('--table_name', help='Name of the table to store the data')
    parser.add_argument('--url', help='URL of the CSV file')

    # Parse the command-line arguments
    args = parser.parse_args()

    # Call the main function with parsed arguments
    main(args)
