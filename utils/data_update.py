import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import numpy as np
import datetime as dt
import time
import os
import glob
import configparser
current_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(current_dir, 'config.ini')
config = configparser.ConfigParser()
config.read('config.ini')
creds_path = config['GoogleAPI']['creds']
default_email = config['Data']['default_email']
file = config['Data']['file']



def pull_competitors(creds, competition):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(creds, scope)
    client = gspread.authorize(creds)

    # Open the Google Spreadsheet using its name
    spreadsheet = client.open(competition)

    # Get a list of all sheet names in the spreadsheet
    sheet_names = spreadsheet.worksheets()
    
    # Initialize an empty DataFrame
    combined_data = pd.DataFrame()
    all_data_frames = []
    # Iterate through all sheets and append data to the DataFrame
    for sheet in sheet_names:
        # Get all values from the sheet
        data = spreadsheet.worksheet(sheet.title).get_all_values()

        # Convert the data to a DataFrame
        sheet_df = pd.DataFrame(data[1:], columns=data[0])
        sheet_df = sheet_df.iloc[:, :2]
        sheet_df['SheetName'] = sheet.title
        all_data_frames.append(sheet_df)

        # Append the sheet data to the combined DataFrame
        combined_data = pd.concat(all_data_frames, ignore_index=True)
        combined_data['Miles'] = combined_data['Miles'].replace({'':0})
        combined_data['Miles'] = combined_data['Miles'].astype(float)
        combined_data['Miles'] = combined_data['Miles'].round(2)
        combined_data['Date'] = pd.to_datetime(combined_data['Date'])
        combined_data.dropna(subset = ['Date'], inplace = True)

    combined_data = combined_data.rename(columns={'SheetName': 'Competitor'})
    return combined_data


# Check if the file exists
def data_check(file_path, creds):
    if os.path.exists(file_path):
        # Get the modification time of the file
        mod_time = os.path.getmtime(file_path)
        # Get the current time
        current_time = time.time()
        # Calculate the difference in seconds
        time_diff = current_time - mod_time
        # Check if the file was modified in the past hour
        if time_diff >= 3600:
            # Run the script
            print("File hasn't been modified in the past hour. Running script...")
            recent_data = pull_competitors(creds, "Workout Competition!")
            recent_data.to_csv(file_path, index = False)
        else:
            print("File has been modified in the past hour. Skipping...")
    else:
        print("File does not exist. Generating new file")
        recent_data = pull_competitors(creds, "Workout Competition!")
        recent_data.to_csv(file_path, index = False)


if __name__ == "__main__":
    data_check(file)