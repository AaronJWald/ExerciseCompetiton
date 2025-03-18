# Exercise Competition
## A Python tool that facilitates competition between users by allowing them to track workout data for individual and group insights.

A Python-based application that tracks, analyzes, and reports on running activities for participants in a fitness competition. This tool automatically generates personalized weekly reports for each competitor, showing their progress, achievements, and standing in relation to other participants.
The application connects to a Google Sheet to retrieve running data, performs various analyses on that data, and generates detailed reports that include:
- Individual weekly and total mileage summaries
- Performance trends and comparisons to personal averages
- Milestone achievements (half-marathon, marathon, ultra-marathon distances)
- Competition rankings and progress needed to advance
- Group statistics and collective achievements

This tool is designed to increase motivation and engagement in running challenges by providing regular, personalized feedback and friendly competition metrics.

You will need a google service account (free) with Google Sheets API enabled and an SMTP account to be able to email the results to each participant.

## Features:
 ### Data Retrieval
 - Automatically pulls running data from Google Sheets using the Google Sheets API
 - Incorporates Apache Airflow DAG's to orchestrate project execution.

 ### Performance Analytics
 - Weekly and total mileage tracking
 - Performance trend analysis compared to personal averages
 - New personal records identification
 - Progress tracking toward milestone goals (half-marathon, marathon, ultra-marathon)

 ### Competition Metrics
 - Leaderboard rankings with current standings
 - Gap analysis showing miles needed to advance in rankings
 - Identification of "strong starters" and other weekly achievements
 - Tracking of top performers and record holders

 ### Motivational Elements
 - Dynamic, personalized feedback based on performance
 - Recognition of achievements and milestones
 - Encouragement for participants who haven't logged miles
 - Side bet tracking between specific competitors
 
 ### Group Statistics:
 - Collective mileage calculations with interesting distance comparisons
 - Daily activity updates showing recent participants
 - Club recognition for distance milestones (half-marathon, marathon, ultra-marathon clubs)

 ### Data Visualization:
 - Performance graphs showing weekly mileage trends
 - Visual representation of individual progress over time

 ### Configurable Settings:
 - Uses configuration files for API credentials and user defaults
 - Customizable report components and messaging

## Installation and configuration
 ### Clone this repository
 ```
 git clone https://github.com/AaronJWald/ExerciseCompetiton.git
 cd Exercise_Competition
 ```
 ### Install Dependencies
 ```
 pip install -r requirements.txt
 ```
 ### Configure config.ini
 - Path to your google api credentials
 - Input your email address and smtp password
 - Make sure to rename the config.example.ini to config.ini

 ### Create a Google Sheet titled "Workout Competition!" with one tab per user, and share it with your google service account

 ### Optional: Set up prod_run_dag to run as desired in Apache Airflow
 - If skipping airflow, "Running Competition" can be ran directly.

