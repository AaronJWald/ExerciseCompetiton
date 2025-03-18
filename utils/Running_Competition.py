import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import numpy as np
import datetime as dt
import os
import matplotlib.pyplot as plt
import warnings
from random import randint
import configparser

# Suppress the DeprecationWarning for the specific line
warnings.filterwarnings("ignore", category=DeprecationWarning, module="Running_Competition.py", lineno=204)

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


class GoogleSheetImporter:
    def __init__(self, credentials_file, sheet_name, user, file):
        # Use credentials to create a gspread authorized client
        self.scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        self.credentials = ServiceAccountCredentials.from_json_keyfile_name(credentials_file, self.scope)
        self.client = gspread.authorize(self.credentials)

        self.competitor_data = pd.read_csv(file)
        self.competitor_data['Miles'] = self.competitor_data['Miles'].replace({'':0})
        self.competitor_data['Miles'] = self.competitor_data['Miles'].astype(float)
        self.competitor_data['Miles'] = self.competitor_data['Miles'].round(2)
        self.competitor_data['Date'] = pd.to_datetime(self.competitor_data['Date'])
        self.user = user
        self.total_miles = self.competitor_data.groupby(by='Competitor', as_index= False).sum(numeric_only=True).sort_values(by='Miles', ascending=False)
        self.longest_run = self.competitor_data.loc[self.competitor_data['Miles'] == self.competitor_data['Miles'].max()]
        self.user_data = self.competitor_data.loc[self.competitor_data['Competitor'] == self.user]
        self.user_longest_run = self.user_data.loc[self.user_data['Miles'] == self.user_data['Miles'].max()]
        self._sheet_name = sheet_name
        self.week_start = dt.date.today() - dt.timedelta(days=7)

    def past_week(self):
        today = dt.date.today()
        week_start = today - dt.timedelta(days=7)
        week = self.competitor_data['Miles'].loc[((self.competitor_data['Date'].dt.date >= week_start) & (self.competitor_data['Competitor'] == self.user))].sum()
        week = round(week,2)
        return week

    def competitors_past_week(self, days = 7):
        days_needed = days
        competitors = self.competitor_data['Competitor'].unique()

        all_comps = [(x, self.competitor_miles_last_week(competitor=x, days_needed = days_needed)) for x in competitors]

        competitor_stats = pd.DataFrame(all_comps, columns=['Competitor', 'Miles'])
        competitor_stats.sort_values(by='Miles', inplace=True, ascending=False)

        competitor_stats = competitor_stats.reset_index()
        competitor_stats['Miles'] = competitor_stats['Miles'].round(2)
        return competitor_stats
    
    
    def read_data_for_competitor(self, competitor):
        """Brings in current DF for a specific competitor with caching"""
        # Fetch data for a specific competitor
        data = self.competitor_data.loc[self.competitor_data['Competitor'] == competitor]
        data['Date'] = pd.to_datetime(data['Date'])

        return data
    
    def competitor_miles_last_week(self, competitor, days_needed):
        ### Returns miles ran by competitor
        data = self.competitor_data.loc[self.competitor_data['Competitor'] == competitor]
        data['Date'] = pd.to_datetime(data['Date'])

        result_sum = data['Miles'].loc[data['Date'].dt.date >= (dt.date.today() - dt.timedelta(days=days_needed))].sum()
        if np.isnan(result_sum):
            return 0
        else:
            return data['Miles'].loc[data['Date'].dt.date >= (dt.date.today() - dt.timedelta(days=days_needed))].sum()

    def week_and_user_graph(self):
        week_user_graph = self.competitor_data.copy()
        week_user_graph['Date'] = week_user_graph['Date'].dt.isocalendar().week

        weekly_distance = week_user_graph.pivot_table(
    index='Date',
    columns='Competitor',
    values='Miles',
    aggfunc='sum',
    fill_value=0  # Fill missing values with 0
).reset_index()
        weekly_distance['Date'] = weekly_distance['Date'] -5 #competition started in week 5, I wanted graph to display week 0
        weekly_distance = weekly_distance.iloc[:-1]
        return weekly_distance
    
    def graph_creator(self):
        plt.style.use('seaborn-v0_8')
        data = self.week_and_user_graph()

        average = data[self.user].mean()
        x = data['Date']
        y = data[self.user]

        # Create the plot
        plt.plot(x, y, marker='o', linestyle='-')
        plt.ylim(ymin = 0)

        # Add labels and title
        plt.xlabel("Week")
        plt.ylabel("Miles Ran")
        plt.title(f"{self.user}'s Past Performance")
        plt.axhline(y=average, color='black', linestyle='-', label = 'Average Miles Ran')
        plt.legend()
        today = dt.date.today().strftime("%Y-%m-%d")
        plt.savefig('figs/' + f"{self.user}_{today}.png")
        plt.clf()
        return 'figs/' + f"{self.user}_{today}.png"


    ### Below consists of output functions indended to be included in the email
    #In the function below, I generate random numbers to pick one of a handful of statements if a condition is meant. This allows people to get unique emails, even if their habits are the same.
    
    def past_week_performance(self):
        y = randint(0,2)
        miles_ran = self.past_week()

        if miles_ran >= 20:
            Outputs = [f"Wow, {miles_ran} miles this week?! That's incredible! You're crushing your goals!\n",
                       f"Absolutely phenomenal work this week with {miles_ran} miles. Keep it up!\n",
                       f"Surpassing 20 miles this week is no small feat! You're an inspiration, keep going strong!\n"]
            Output2 = f"You ran {miles_ran} miles this past week and {round(self.total_miles['Miles'].loc[self.total_miles['Competitor'] == self.user].item(),2)} miles in total. \n\n"
        elif ((miles_ran < 20) & (miles_ran >= 10)):
            Outputs = [f"Fantastic effort this week! Hitting {miles_ran} miles is a great accomplishment, keep it rolling!\n",
                    f"Double-digit miles, impressive! You're putting in some serious work.\n",
                    f"You broke 10 miles this week! Keep going strong.\n"]
            Output2 = f"You ran {miles_ran} miles this past week and {round(self.total_miles['Miles'].loc[self.total_miles['Competitor'] == self.user].item(),2)} miles in total. \n\n"
        elif ((miles_ran < 10) & (miles_ran >= 5)):
            Outputs = [f"Nice work putting in some solid miles this week! Keep it up and you'll reach your goals in no time.\n",
                       f"Those workouts this week are adding up! Let's see you push yourself even further next week.\n",
                       f"It's awesome to see you logged your workouts! Every effort counts, keep pushing yourself.\n"]
            Output2 = f"You ran {miles_ran} miles this past week and {round(self.total_miles['Miles'].loc[self.total_miles['Competitor'] == self.user].item(),2)} miles in total. \n\n"
        elif ((miles_ran < 5) & (miles_ran > 0)):
            Outputs = [f"Great job logging your workouts this week. Consistency is key to progress, keep it up!\n",
                       f"Glad to see you logged some workouts this week! Need any help planning your next workout?\n",
                       f"It's awesome to see you logged your workouts! Every effort counts, keep pushing yourself.\n"]
            Output2 = f"You ran {miles_ran} miles this past week and {round(self.total_miles['Miles'].loc[self.total_miles['Competitor'] == self.user].item(),2)} miles in total. \n\n"
        else:
            Output1 = "Looks like you didn't log any miles last week. Enter some workouts to get recognition for your efforts and how they compare to everyone else's!\n"
            Output2 = ''
            return Output1 + Output2

        Output1 = Outputs[y]
        return Output1 + Output2

    def trending(self):
        y = randint(0,2)
        data = self.week_and_user_graph()
        if data['Date'].max() < 3:
            return ''
        recent_data = data.iloc[-3:]
        average = data[self.user].mean()
        recent_average = recent_data[self.user].mean()
        past_week = data[self.user].iloc[-1]

        if past_week > average:
            ###Fill in past week vs. average
            Outputs_weekly = [f"You beat your average miles ran.\n",
                       f"You put in some extra effort and beat your average calories burned.\n",
                       f"You surpassed your average calories burned. Nicely done.\n"]
        elif ((past_week < average) & (past_week > 0)):
            Outputs_weekly = [f"You didn't quite reach your average calories burned.\n",
                       f"You were below your average calories burned.\n",
                       f"You burned less calories than usual.\n"]
        else:
            Outputs_weekly = ['','','']
            ###Fill in past week vs. average
        y = randint(0,2)
        if recent_average > (average * 1.2):
            Outputs = [f"Your workout intensity has been trending up lately, great work!\n",
                       f"Look at you pushing your limits. Your workout intensity is on the up and up!\n",
                       f"There has been a noticeable jump in your workout intensity lately, great work!\n"]
        if ((recent_average >= (average * 0.8)) & (recent_average <= (average * 1.2))):
            Outputs = [f"Your recent workout trend is on par with your average.\n",
                       f"Your workout intensity has been stable in recent weeks.\n",
                       f"There hasn't been a change in trend for your workout intensity lately\n"]
        if recent_average < (average * 0.8):
            Outputs = [f"Your workout intensity has been trending down lately.\n",
                       f"You've been working out less in recent weeks.\n",
                       f"Looks like your workout intensity has slipped in recent weeks.\n"]
        if average > 0:
            if round(average*1.2,1) > 5:
                end_goal = f"To start pushing yourself harder you should aim to log over {round(average*1.2,1)} miles this next week. To maintain your pace, aim to log at least {round(average*0.8,1)}. \n\n"
            else:
                end_goal = f"Let's try to hit 5 miles this next week.  \n\n"
        else:
            end_goal = ''
        
        if (((past_week < average) & (past_week > 0)) & (recent_average > (average * 1.2))):
            return Outputs_weekly[y] + 'That said, your overall workout intensity these past few weeks is still up compared to where you were at the beginning of the competition. Great work!\n' + end_goal
        if (((past_week > average) & (past_week > 0)) & (recent_average < (average * 0.8))):
            return Outputs_weekly[y] + 'However, ' + Outputs[y].lower() + 'Put together another solid week to watch your averages climb! '+ end_goal
        return Outputs_weekly[y] + Outputs[y] + end_goal



    def new_record(self):
        #self.week_start
        date = self.user_longest_run['Date'].loc[self.user_longest_run['Competitor'] == self.user].tolist()
        date = date[0]

        if self.user_longest_run['Miles'].iloc[0] > 0.5:
            if pd.to_datetime(date) >= pd.to_datetime(self.week_start):
                return f"Your {self.user_longest_run['Miles'].iloc[0]} mile run was a new record for you! Way to push yourself harder this week.\n\n"
            else:
                return ''
        else:
            return ''
        


    def new_top_3(self):
        today_date = dt.datetime.combine(dt.date.today(), dt.time(hour=20, minute=0))

        seven_days_ago = today_date - dt.timedelta(days=6)

        top3_today = self.total_miles.nlargest(3, 'Miles')['Competitor'].tolist()

        past_miles = self.competitor_data.loc[(self.competitor_data['Date'] <= seven_days_ago)]
        past_miles = past_miles.groupby(by='Competitor', as_index= False).sum(numeric_only=True).sort_values(by='Miles', ascending=False)

        top3_seven_days_ago = past_miles.nlargest(3, 'Miles')['Competitor'].tolist()
        num_different_names = len(set(top3_today) - set(top3_seven_days_ago))


        if num_different_names == 3:
            return f"The top 3 completely changed this past week, here's your new top 3!\n"
        if num_different_names == 2:
            return f"We've got some movement in the top 3! Two new names appeared since last week.\n"
        if num_different_names == 1:
            new_user = set(top3_today) - set(top3_seven_days_ago)
            old_user = set(top3_seven_days_ago) - set(top3_today)
            return f"{list(new_user)[0]} is replacing {list(old_user)[0]} in the top 3 this week!\n"
        if num_different_names == 0:
            return ''
    
    def competitors_performance(self):
    ### Returns sentence comparing user's miles to others
        other_competitors = self.total_miles.reset_index()

        other_competitors_tie = other_competitors.drop(other_competitors.loc[other_competitors['Competitor'] == self.user].index)
        placement = {1: 'first',2:'second',3:'third',4:'fourth',5:'fifth',6:'sixth',7:'seventh',8:'eighth',9:'ninth',10:'tenth',11:'eleventh',12:'twelfth',13:'thirteenth', 14:'fourteenth', 15:'fifteenth'}
        #print(other_competitors['Competitor'])
        place = other_competitors.index[other_competitors['Competitor'] == self.user].tolist()[0]

        counter = 1
        tied = False  # Use boolean instead of string
        if round(self.total_miles['Miles'].loc[self.total_miles['Competitor'] == self.user].item(),2) > 0:
            for x in other_competitors_tie['Miles']:
                if self.past_week == int(x):
                    tied = True
            if tied:
                output2 = f"You are tied for {placement.get(place+ 1)}.\n"
            else:
                output2 = f"You are currently in {placement.get(place+ 1)} place.\n"
        else:
            output2 = '\n'

        return output2  # Add a space for better readability


    
    def top_3(self):
        other_competitors = self.total_miles
        other_competitors['Miles'] = other_competitors['Miles'].round(2)

        return f"{other_competitors['Competitor'].iloc[0]} is currently in first with {other_competitors['Miles'].iloc[0]} miles ran\n\
{other_competitors['Competitor'].iloc[1]} is currently in second with {other_competitors['Miles'].iloc[1]} miles ran\n\
{other_competitors['Competitor'].iloc[2]} is currently in third with {other_competitors['Miles'].iloc[2]} miles ran\n\n"
    
    def longest_i_run(self):
        return f"{self.longest_run['Competitor'].iloc[0]} has the record for the longest single run of the competition at {self.longest_run['Miles'].iloc[0]} miles.\n\n"

    def strong_starters(self):
        other_competitors = self.competitors_past_week
        strong_starter = other_competitors['Competitor'].loc[other_competitors['Miles'] > 4.0].to_list()
        if len(strong_starter) > 2:
            return f"{''.join([x + ', ' for x in strong_starter[:-1]])}and {strong_starter[-1]} are in our strong starters group! (More than 4 miles since the challenge began)\n\n"
        if len(strong_starter) == 2:
            return f"{''.join([x + ' ' for x in strong_starter[:-1]])}and {strong_starter[-1]} are in our strong starters group! (More than 4 miles since the challenge began)\n\n"
        elif len(strong_starter) == 1:
            return f"{strong_starter[-1]} is the only one in our strong starters group! (More than 4 miles since the challenge began)\n\n"
    
    def zeroes(self):
        other_competitors = self.competitors_past_week()
        zeroes = other_competitors['Competitor'].loc[other_competitors['Miles'] == 0].to_list()

        if len(zeroes) > 2:
            return f"{''.join([x + ', ' for x in zeroes[:-1]])}and {zeroes[-1]} didn't log any miles this week, please give them some encouragement!\n"
        if len(zeroes) == 2:
            return f"{''.join([x + ' ' for x in zeroes[:-1]])}and {zeroes[-1]} didn't log any miles this week, please give them some encouragement!\n"
        elif len(zeroes) == 1:
            return f"{zeroes[-1]} is our only zero mile runner this week, please give them some extra encouragement!\n"
        else:
            return ''
        
    def ultramarathoners(self):
        marathoner_total = self.total_miles['Competitor'].loc[self.total_miles['Miles'] >= 50.0].to_list()
        already_achieved = self.competitor_data.loc[self.competitor_data['Date'].dt.date < self.week_start]
        already_achieved = already_achieved.groupby(by='Competitor', as_index= False).sum(numeric_only=True).sort_values(by='Miles', ascending=False)
        already_achieved = already_achieved['Competitor'].loc[already_achieved['Miles'] >= 50.0].to_list()
        marathoner = [i for i in marathoner_total if i not in already_achieved]




        if len(marathoner) >= 3:
            output1 = f"{''.join([x + ', ' for x in marathoner[:-1]])}and {marathoner[-1]} are joining the ultra-marathoner club! They've ran more than 50 miles since the challenge began! Congratulations to all of them on that achievement.\n"
        elif len(marathoner) == 2:
            output1 = f"{''.join([x + ' ' for x in marathoner[:-1]])}and {marathoner[-1]} are joining the ultra-marathoner club! They've ran more than 50 miles since the challenge began! Congratulations to them on that achievement.\n"
        elif len(marathoner) == 1:
            output1 = f"{marathoner[-1]} is joining the ultra-marathoner club! They've ran over 50 miles since the challenge began!\n"
        else:
            output1 =  ''
        
        if len(marathoner_total) >= 3:
            output2 = f"Ultra-Marathoner Club: {''.join([x + ', ' for x in marathoner_total[:-1]])}and {marathoner_total[-1]}\n"
        elif len(marathoner_total) == 2:
            output2 = f"Ultra-marathoner Club: {''.join([x + ' ' for x in marathoner_total[:-1]])}and {marathoner_total[-1]}\n"
        elif len(marathoner_total) == 1:
            output2 = f"Ultra-marathoner Club: {marathoner_total[-1]}\n"
        else:
            output2 =  ''
        
        return [output1, output2]

    def marathoners(self):
        marathoner_total = self.total_miles['Competitor'].loc[((self.total_miles['Miles'] < 50.0) & (self.total_miles['Miles'] >= 26.2))].to_list()
        already_achieved = self.competitor_data.loc[self.competitor_data['Date'].dt.date < self.week_start]
        already_achieved = already_achieved.groupby(by='Competitor', as_index= False).sum(numeric_only=True).sort_values(by='Miles', ascending=False)
        already_achieved = already_achieved['Competitor'].loc[((already_achieved['Miles'] < 50.0) & (already_achieved['Miles'] >= 26.2))].to_list()
        marathoner = [i for i in marathoner_total if i not in already_achieved]



        if len(marathoner) >= 3:
            output1 = f"{''.join([x + ', ' for x in marathoner[:-1]])}and {marathoner[-1]} are joining the marathoner club! They've ran more than 26.2 miles since the challenge began. Congratulations to all of them on that achievement.\n\n"
        elif len(marathoner) == 2:
            output1 = f"{''.join([x + ' ' for x in marathoner[:-1]])}and {marathoner[-1]} are joining the marathoner club! They've ran more than 26.2 miles since the challenge began. Congratulations to them on that achievement.\n\n"
        elif len(marathoner) == 1:
            output1 = f"{marathoner[-1]} is joining the marathoner club! They've ran over 26.2 miles since the challenge began!\n"
        else:
            output1 =  ''
        
        if len(marathoner_total) >= 3:
            output2 = f"Marathoner Club: {''.join([x + ', ' for x in marathoner_total[:-1]])}and {marathoner_total[-1]}\n"
        elif len(marathoner_total) == 2:
            output2 = f"{''.join([x + ' ' for x in marathoner_total[:-1]])}and {marathoner_total[-1]} are joining the marathoner club! They've ran more than 26.2 miles since the challenge began. Congratulations to them on that achievement.\n\n"
        elif len(marathoner_total) == 1:
            output2 = f"{marathoner_total[-1]} is joining the marathoner club! They've ran over 26.2 miles since the challenge began!\n"
        else:
            output2 =  ''
        
        return [output1, output2]


    def half_marathoners(self):
        marathoner = self.total_miles['Competitor'].loc[((self.total_miles['Miles'] < 26.2) & (self.total_miles['Miles'] >= 13.1))].to_list()
        already_achieved = self.competitor_data.loc[self.competitor_data['Date'].dt.date < self.week_start]
        already_achieved = already_achieved.groupby(by='Competitor', as_index= False).sum(numeric_only=True).sort_values(by='Miles', ascending=False)
        already_achieved = already_achieved['Competitor'].loc[((already_achieved['Miles'] < 26.2) & (already_achieved['Miles'] >= 13.1))].to_list()
        marathoner = [i for i in marathoner if i not in already_achieved]

        if len(marathoner) > 2:
            return f"{''.join([x + ', ' for x in marathoner[:-1]])}and {marathoner[-1]} are joining the half-marathoner club! They've ran more than 13.1 miles since the challenge began. Incredible work and keep going!\n\n"
        elif len(marathoner) == 2:
            return f"{''.join([x + ' ' for x in marathoner[:-1]])}and {marathoner[-1]} are joining the half-marathoner club! They've ran more than 13.1 miles since the challenge began. Incredible work and keep going!\n\n"
        elif len(marathoner) == 1:
            return f"{marathoner[-1]} is joining the half-marathoner club! Awesome work!\n\n"
        else:
            return ''

        

    def next_competitor(self):
        current_place = self.total_miles['Competitor'].to_list().index(str(self.user))
        placement = {1: 'first',2:'second',3:'third',4:'fourth',5:'fifth',6:'sixth',7:'seventh',8:'eighth',9:'ninth',10:'tenth',11:'eleventh',12:'twelfth',13:'thirteenth', 14:'fourteenth', 15:'fifteenth'}

        user_place = current_place + 1
        #user place isn't 0 indexed so add one to retrieve proper place
        user_miles = round(self.total_miles['Miles'].loc[self.total_miles['Competitor'] == self.user].item(),2)
        
        if ((user_place > 1) & (user_place < (len(self.total_miles['Competitor'].to_list()) + 1)) & (user_miles != 0)):
            next_user = self.total_miles['Competitor'].iloc[current_place -1]
            ### minus 1 to get spot earlier in list
            next_miles = self.total_miles['Miles'].iloc[current_place-1]
            next_place = placement.get(current_place)
            behind_miles = self.total_miles['Miles'].iloc[current_place+1]
            behind_user = self.total_miles['Competitor'].iloc[current_place +1]

            return f"You are currently in {placement.get(user_place)}. To surpass {next_user} and enter {next_place} place, you need to run {round(next_miles - user_miles,2)} more miles than them before Monday. You are only {round(user_miles - behind_miles,2)} miles ahead of {behind_user}.\n\n"
        elif user_place == 1:
            next_miles = self.total_miles['Miles'].iloc[current_place+1]
            return f"Keep it up! You only have {round(user_miles - next_miles,2)} separating you from second place. \n\n"
        elif user_place == (len(self.total_miles['Competitor'].to_list()) + 1):
            next_user = self.total_miles['Competitor'].iloc[current_place -1]
            ### minus 1 to get spot earlier in list
            next_miles = self.total_miles['Miles'].iloc[current_place-1]
            next_place = placement.get(current_place)
            return f"You are currently in last place. To surpass {next_user} and enter {next_place} place, you need to run {round(next_miles - user_miles,2)} more miles than them before Monday.\n\n "
        elif user_miles == 0:
            next_user = self.total_miles['Competitor'].iloc[current_place -1]
            ### minus 1 to get spot earlier in list
            next_miles = self.total_miles['Miles'].iloc[current_place-1]
            next_place = placement.get(current_place)
            return f"You are currently in last place. To surpass {next_user} and enter {next_place} place, you need to run {round(next_miles - user_miles,2)} more miles than them before Monday.\n\n "
        else:
            return ''
        
        
    def next_competitor_wr(self):
        current_place = self.total_miles['Competitor'].to_list().index(str(self.user))
        placement = {1: 'first',2:'second',3:'third',4:'fourth',5:'fifth',6:'sixth',7:'seventh',8:'eighth',9:'ninth',10:'tenth',11:'eleventh',12:'twelfth',13:'thirteenth', 14:'fourteenth', 15:'fifteenth'}

        user_place = current_place + 1
        #user place isn't 0 indexed so add one to retrieve proper place
        user_miles = round(self.total_miles['Miles'].loc[self.total_miles['Competitor'] == self.user].item(),2)

        if user_miles == 0:
            return 'Placement in the competition will be tracked once you log your first workout.\n\n'
        
        if ((user_place > 1) & (user_place < (len(self.total_miles['Competitor'].to_list()) + 1))):
            next_user = self.total_miles['Competitor'].iloc[current_place -1]
            ### minus 1 to get spot earlier in list
            next_miles = self.total_miles['Miles'].iloc[current_place-1]
            next_place = placement.get(current_place)
            behind_miles = self.total_miles['Miles'].iloc[current_place+1]
            behind_user = self.total_miles['Competitor'].iloc[current_place +1]

            return f"To surpass {next_user} and enter {next_place} place, you need to run {round(next_miles - user_miles,2)} more miles than them this week.\n\n"
        elif user_place == 1:
            next_miles = self.total_miles['Miles'].iloc[current_place+1]
            return f"You are in first, keep it up! You only have {round(user_miles - next_miles,2)} separating you from second place\n\n"
        elif user_place == (len(self.total_miles['Competitor'].to_list()) + 1):
            next_user = self.total_miles['Competitor'].iloc[current_place -1]
            ### minus 1 to get spot earlier in list
            next_miles = self.total_miles['Miles'].iloc[current_place-1]
            next_place = placement.get(current_place)
            return f"This is last place. To surpass {next_user} and enter {next_place} place, you need to run {round(next_miles - user_miles,2)} more miles than them this week. \n\n"
        elif user_miles == 0:
            next_user = self.total_miles['Competitor'].iloc[current_place -1]
            ### minus 1 to get spot earlier in list
            next_miles = self.total_miles['Miles'].iloc[current_place-1]
            next_place = placement.get(current_place)
            return f"This is last place. To surpass {next_user} and enter {next_place} place, you need to run {round(next_miles - user_miles,2)} more miles than them this week. \n\n"
        else:
            return ''        
    def goals(self):
        miles = round(self.total_miles['Miles'].loc[self.total_miles['Competitor'] == self.user].item(),2)

        if miles >= 50:
            return "You've already achieved the ultra-marathon group, amazing!"
        if ((miles < 50) & (miles >= 26.2)):
            return f"You've already achieved the marathoner group. Awesome work! Push yourself {round(50 - miles,2)} more miles to enter the Ultra-marathon group!"
        if ((miles < 26.2) & (miles >= 13.1)):
            return f"You've already achieved the half-marathoner group. Awesome work! Push yourself {round(26.2 - miles,2)} more miles to become part of the marathoner group!"
        if ((miles < 13.1) & (miles > 8)):
            return f"You're almost there! Push yourself {round(13.1 - miles,2)} more miles to become part of the half-marathoner group!"
        else:
            return ''
        
    def sidebet(self,other):
        competitor_miles = self.total_miles['Miles'].loc[self.total_miles['Competitor'] == self.user].item()
        other_miles = self.total_miles['Miles'].loc[self.total_miles['Competitor'] == other].item()
        if competitor_miles > other_miles:
            return f'In your side bet, you are ahead of {other} by {round(competitor_miles - other_miles,2)} miles'
        else:
            return f'In your side bet, you are behind {other} by {round(other_miles - competitor_miles,2)} miles'
    
    def all_miles(self):
        all = self.total_miles["Miles"].sum()
        cities = pd.read_csv('files/Distances.csv')
        cities['True_Distance'] = cities['Distance'] - all
        cities['Absolute_distance'] = cities['True_Distance'].abs()
        close_cities = cities.loc[((cities['Distance'] > 0.97*all) & (cities['Distance'] < 1.03*all))]
        if ((self.user in ['User_1', 'User_2']) & ('Fargo' in close_cities['City1'].tolist())):
            close_cities = close_cities.loc[close_cities['City1'] == 'Fargo']
        if ((self.user in ['User_3', '4']) & ('Peoria' in close_cities['City1'].tolist())):
            close_cities = close_cities.loc[close_cities['City1'] == 'Peoria']
        if ((self.user in ['User_5', 'User_6','User_7','User_8']) & ('Madison' in close_cities['City1'].tolist())):
            close_cities = close_cities.loc[close_cities['City1'] == 'Madison']
        if ((self.user in ['User_9']) & ('Dartmouth' in close_cities['City1'].tolist())):
            close_cities = close_cities.loc[close_cities['City1'] == 'Dartmouth']
        if len(close_cities) == 0:
            return f"So far we have ran a collective {round(all,2)} miles!\n\n"
        if len(close_cities) == 1:
            return f"We've ran a collective {round(all,2)} miles. This is about the distance from {close_cities['City1'].iloc[0]} to {close_cities['City2'].iloc[0]}.\n\n"
        else:
            y = randint(0,(len(close_cities) -1))

            return f"We've ran a collective {round(all,2)} miles. This is about the distance from {close_cities['City1'].iloc[y]} to {close_cities['City2'].iloc[y]}.\n\n"
    

    def daily_update(self):
        today = dt.date.today()
        runners = self.competitors_past_week(days= 1)
        runners = runners.loc[runners['Miles'] > 0]
        runners = runners['Competitor'].to_list()


        if len(runners) > 2:
            return f"{''.join([x + ', ' for x in runners[:-1]])}and {runners[-1]} logged a workout in the past 24 hours"
        elif len(runners) == 2:
            return f"{''.join([x + ' ' for x in runners[:-1]])}and {runners[-1]} logged a workout in the past 24 hours"
        elif len(runners) == 1:
            return f"{runners[-1]} logged a workout in the past 24 hours"
        else:
            return 'No one logged a workout in the past day'


if __name__ == "__main__":
    users_GP = pd.read_csv(file)['Competitor'].unique()
    for x in users_GP:
        GP_challenge = GoogleSheetImporter(creds_path, "Workout Competition!",x,file)
        subject = f"{x}'s weekly running report."
        message_2 = f"Hey {x}, here is your weekly report.\n\n"
        message = (message_2 + GP_challenge.past_week_performance() + GP_challenge.trending() + GP_challenge.new_record() + GP_challenge.new_top_3() + GP_challenge.top_3() \
                + GP_challenge.ultramarathoners()[0]+  GP_challenge.marathoners()[0]+ GP_challenge.half_marathoners()+ GP_challenge.longest_i_run()+ GP_challenge.ultramarathoners()[1]+ GP_challenge.marathoners()[1] + GP_challenge.all_miles()+  GP_challenge.zeroes())
        print(message)
