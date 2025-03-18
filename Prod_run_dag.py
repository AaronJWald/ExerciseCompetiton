from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
from random import randint
import pandas as pd
import gspread
# import sys
import os
import glob
import time
# sys.path.insert(0,os.path.abspath(os.path.dirname(__file__)))
from utils import data_update
from utils import Email_Python
from utils import Users_email
from utils import Running_Competition
import configparser


current_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(current_dir, 'config.ini')
config = configparser.ConfigParser()
config.read('config.ini')
creds_path = config['GoogleAPI']['creds']
default_email = config['Data']['default_email']
file = config['Data']['file']


# Define the DAG

# Define tasks (replace these with your actual Python functions)

def task_1():
    '''Uses utility to pull data from google and save it locally, allowing for greater flexibility in processing.'''
    data_update.data_check(file,creds_path)

def task_2():
  Addresses = Users_email.Contact_Importer(creds_path, 'contacts').data_to_dict()
  #Incorporate addresses
  """
  This function reads data and provides insights
  """
  users_GP = pd.read_csv(file)['Competitor'].unique()
  users_GP = users_GP.tolist()
  for x in users_GP:
    GP_challenge = Running_Competition.GoogleSheetImporter(creds_path, "Workout Competition!",x,file)
    subject = f"{x}'s weekly running report."
    message_2 = f"Hey {x}, here is your weekly report.\n\n"
    message = (message_2 + GP_challenge.past_week_performance() + GP_challenge.trending() + GP_challenge.new_record() + GP_challenge.new_top_3() + GP_challenge.top_3() \
                + GP_challenge.ultramarathoners()[0]+  GP_challenge.marathoners()[0]+ GP_challenge.half_marathoners()+ GP_challenge.longest_i_run()+ GP_challenge.ultramarathoners()[1]+ GP_challenge.marathoners()[1] + GP_challenge.all_miles())
    Email_Python.send_email(subject=subject,body = message, to_email= Addresses.get(x),filename = GP_challenge.graph_creator())
    time.sleep(0.5)

#Update start date to reflect when you want to run the program
with DAG(
  dag_id="prod_run_dag",
  default_args={"owner": "airflow", "start_date": datetime(2024, 3, 18)},  # Set a fixed date
  schedule_interval="0 1 * * TUE", catchup= False # Run manually
) as dag:
  task1 = PythonOperator(
      task_id='data_update',
      python_callable=task_1,
  )

  task2 = PythonOperator(
      task_id='transform_and_send',
      python_callable=task_2,
  )

  task1 >> task2


