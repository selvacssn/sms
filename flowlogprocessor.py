import os
import gzip
import pandas as pd
import mysql.connector
import shutil

# Database connection
def connect_db():
    return mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="Global!23",
        database="AWS"
    )

# Insert data into the database
def insert_data(cursor, data, batch_size=1000):
    insert_query = """
    INSERT INTO aws_flow_logs (
        version, account_id, interface_id, srcaddr, dstaddr, srcport, dstport, protocol,
        packets, bytes, start, end, action, log_status
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    for i in range(0, len(data), batch_size):
        batch = data[i:i + batch_size]
        cursor.executemany(insert_query, batch)


# Get all subdirectories with full paths
def get_all_subdirectories(directory):
    subdirectories = []
    for root, dirs, files in os.walk(directory):
        for dir in dirs:
            subdirectories.append(os.path.join(root, dir))
    return subdirectories

def process_gz_files(root_directory):
    conn = connect_db()
    cursor = conn.cursor()
    
    subdirectories = get_all_subdirectories(root_directory)
    for subdirectory in subdirectories:
        for root, dirs, files in os.walk(subdirectory):
            for file in files:
                if file.endswith(".gz"):
                    gz_path = os.path.join(root, file)
                    with gzip.open(gz_path, "rt") as f:
                        try:
                            df = pd.read_csv(f, delim_whitespace=True, header=None, skiprows=1)
                            df.columns = [
                                'version', 'account_id', 'interface_id', 'srcaddr', 'dstaddr',
                                'srcport', 'dstport', 'protocol', 'packets', 'bytes', 'start',
                                'end', 'action', 'log_status'
                            ]
                            """df['version'] = df['version'].astype(int)
                            df['srcport'] = df['srcport'].astype(int)
                            df['dstport'] = df['dstport'].astype(int)
                            df['protocol'] = df['protocol'].astype(int)
                            df['packets'] = df['packets'].astype(int)
                            df['bytes'] = df['bytes'].astype(int)
                            df['start'] = df['start'].astype(int)
                            df['end'] = df['end'].astype(int)"""
                            data = df.values.tolist()
                            insert_data(cursor, data)
                            conn.commit()
                        except Exception as e:
                            print(f"Error processing file {gz_path}: {e}")
    
    cursor.close()
    conn.close()


def extract_gz_files(root_directory, temp_directory):
    subdirectories = get_all_subdirectories(root_directory)
    for subdirectory in subdirectories:
        for root, dirs, files in os.walk(subdirectory):
            for file in files:
                if file.endswith(".gz"):
                    gz_path = os.path.join(root, file)
                    with gzip.open(gz_path, "rt") as f_in:
                        csv_filename = os.path.splitext(file)[0] + ".csv"
                        csv_path = os.path.join(temp_directory, csv_filename)
                        with open(csv_path, "wt") as f_out:
                            shutil.copyfileobj(f_in, f_out)

# Load CSV files into MySQL
def load_csv_to_mysql(temp_directory):
    conn = connect_db()
    cursor = conn.cursor()
    
    for root, dirs, files in os.walk(temp_directory):
        for file in files:
            print(file)
            if file.endswith(".csv"):
                csv_path = os.path.join(root, file)
                load_data_query = f"""
                LOAD DATA INFILE '{csv_path}'
                INTO TABLE aws_flow_logs
                FIELDS TERMINATED BY ' '
                LINES TERMINATED BY '\n'
                IGNORE 1 LINES
                (version, account_id, interface_id, srcaddr, dstaddr, srcport, dstport, protocol,
                packets, bytes, start, end, action, log_status);
                """
                cursor.execute(load_data_query)
                conn.commit()
    
    cursor.close()
    conn.close()

# Main function to start the processing
if __name__ == "__main__":
    root_directory = "C:\\Users\\SenthilSelvaNivasC\\workspace\\flowlog\\07\\24"
    #process_gz_files(root_directory)
    #root_directory = "/path/to/your/root/directory"
    #temp_directory = "C:\\Users\\SenthilSelvaNivasC\\workspace\\flowlog\\07\\24\\csvs"
    temp_directory = "//var//lib//mysql-files//"
    
    # Create the temporary directory if it doesn't exist
    #os.makedirs(temp_directory, exist_ok=True)
    
    # Extract gz files to temporary directory
    #extract_gz_files(root_directory, temp_directory)
    
    # Load CSV files into MySQL
    load_csv_to_mysql(temp_directory)
    
    # Optionally, clean up the temporary directory
    #shutil.rmtree(temp_directory)
