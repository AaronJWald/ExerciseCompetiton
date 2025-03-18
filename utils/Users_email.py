import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import datetime as dt
import os
import configparser
current_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(current_dir, 'config.ini')
config = configparser.ConfigParser()
config.read('config.ini')
creds_path = config['GoogleAPI']['creds']
default_email = config['Data']['default_email']
file = config['Data']['file']

class Contact_Importer:
    def __init__(self, credentials_file, sheet_name):
        # Use credentials to create a gspread authorized client
        pass
    def data_to_dict(self):
        #worksheet = self.sheet.worksheet('Sheet1') #### This was used previously to live pull contact data, but since the contest remains the same people, I can just utilize a copy of thisd ata
        data = pd.read_csv(file)
        data_df = pd.DataFrame(data)
        data_dict = data_df.set_index('User')['Email'].to_dict()
        return data_dict
    def all_users(self):
        #worksheet = self.sheet.worksheet('Sheet1')
        #data = worksheet.get_all_records()
        data = pd.read_csv(file)
        data_df = pd.DataFrame(data)
        User_list = data_df['User'].to_list()
        return User_list
    def save_data(self,sheet_name):
        worksheet = self.client.open(sheet_name).worksheet('Sheet1')
        data = worksheet.get_all_records()
        data_df = pd.DataFrame(data)
        data_df.to_csv(file, index=False)

#users = Contact_Importer(creds,'contacts').save_data('contacts')

