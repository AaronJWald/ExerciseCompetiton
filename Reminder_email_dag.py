from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import time
import pandas as pd
import gspread
# import sys
import os
import glob
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
    data_update.data_check(file,creds_path)

def task_2():
  Minneapolis_link = "google_docs_link"
  Madison_link = "google_docs_link2"

  challenge_config = {
    'Minneapolis': {'link': Minneapolis_link, 'name': "Minneapolis running challenge"},
    'Madison': {'link': Madison_link, 'name': 'Potluck running challenge'}
}
  def generate_running_challenge_message(name, link):
      return f"Hey {name}, you are getting this message because you currently have 0 miles logged this week for the running challenge. Log your miles before Monday to get included in the summary email. Here is the link! \n\n{link}"
  Addresses = Users_email.Contact_Importer(creds_path, 'contacts').data_to_dict()
  users_GP = pd.read_csv(file)['Competitor'].unique()
  for x in users_GP:
    GP_challenge = Running_Competition.GoogleSheetImporter(creds_path, "Workout Competition!",x,file)
    subject = f"{x}'s weekend workout goal"
    challenge_name = 'Minneapolis'  # Replace with logic to determine the challenge name
    config = challenge_config.get(challenge_name, {})

    if GP_challenge.past_week() > 0:
        message = GP_challenge.next_competitor() + GP_challenge.goals() +' Here is the link to post your miles. Keep going!\n' + Minneapolis_link
    else:
        message = generate_running_challenge_message(x, Minneapolis_link) +'\n\n' + GP_challenge.goals()

    #remember to update file
    Email_Python.send_email(subject=subject, body=message, to_email=Addresses.get(x))
    time.sleep(0.5)



with DAG(
  dag_id="reminder_run_dag",
  default_args={"owner": "airflow", "start_date": datetime(2024, 3, 18)},  # Set a fixed date
  schedule_interval="0 23 * * FRI", catchup= False  # Run manually
) as dag:
  task1 = PythonOperator(
      task_id='data_update_reminder',
      python_callable=task_1,
  )

  task2 = PythonOperator(
      task_id='transform_and_send',
      python_callable=task_2,
  )

task1 >> task2

  #good
