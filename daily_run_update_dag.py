from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
from random import randint
import pandas as pd
import gspread
import os
import glob
from utils import data_update
from utils import Email_Python
from utils import gpt_run_2
import configparser

current_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(current_dir, 'config.ini')
config = configparser.ConfigParser()
config.read('config.ini')
creds_path = config['GoogleAPI']['creds']
default_email = config['Data']['default_email']
file = config['Data']['file']


def task_1():
    file_path = file
    data_update.data_check(file_path,creds_path)

def task_2():
  '''This updates the data and informs me when the update is run.'''
  GP_challenge = gpt_run_2.GoogleSheetImporter(creds_path, "Workout Competition!",'Aaron',file)
  subject = 'Daily update'
  message = GP_challenge.daily_update()

  Email_Python.send_email(subject=subject,body = message, to_email= default_email)


with DAG(
  dag_id="daily_update",
  default_args={"owner": "airflow", "start_date": datetime(2024, 3, 18)},  # Set a fixed date
  schedule_interval="30 0 * * *", 
  catchup=False # Run manually
) as dag:
  task1 = PythonOperator(
      task_id='run_query',
      python_callable=task_1,
  )

  task2 = PythonOperator(
      task_id='interpret',
      python_callable=task_2,
  )

task1 >> task2
