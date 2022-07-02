import subprocess

subprocess.run(['pip','install','-r','requirements.txt'])

import requests
from bs4 import BeautifulSoup
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from selenium.webdriver.common.by import By
import pandas as pd
import os
import shutil
import tkinter as tk
from tkinter import ttk
from fastDamerauLevenshtein import damerauLevenshtein
import jaro
import plotly.express as px

# def find_file_loc(name, path):
#     """Searches for a file within subdirectories of given path. Returns file path of file if found or raises
#     exception if no file found"""
#     print(f"Attempting to find '{name}'. This may take a while depending on size of subdirectories in '{path}'")
#     for root, dirs, files in os.walk(path):
#         if name in files:
#             print(f"Found '{name}'")
#             return os.path.join(root, name)
#     raise Exception(f"'{name}' could not be found anywhere within '{path}'")

# home_dir = os.path.expanduser('~') # Get user's home directory
# target_dir = os.path.join(home_dir,'xg_analysis') # Add xg_analysis onto end of user directory path

# # If xg_analysis folder does not exist in the home directory yet, creates it
# if 'xg_analysis' not in [val.name for val in os.scandir(home_dir)]:
#     print(f"'{target_dir}' does not exist. Creating folder in '{home_dir}' now")
#     os.mkdir(target_dir)

# # Searching for chromedriver to be used to gather data from fbref
# if 'chromedriver' not in [val.name for val in os.scandir(target_dir)]:
#     try:
#         print(f"chromedriver does not exist in '{target_dir}' directory. Starting process to find and move it now")
#         chrome_driver_path = find_file_loc('chromedriver',home_dir) # Searches for chromedriver within user directory
#         new_file = os.path.join(target_dir,'chromedriver') # Creates path for where chromedriver should be for use later on (xg_analysis folder)
#         print('Moving across chromedriver to folder')
#         subprocess.run(['mv',f'{chrome_driver_path}',f'{new_file}']) # Moves chromedriver from existing location to xg_analysis folder
#     except Exception as e:
#         print(e) # Exception from find_file_loc function
#         print('Make sure you have installed selenium and downloaded chromedriver')
#         print('chromedriver can be downloaded at https://chromedriver.chromium.org/downloads')

# print('Setup of necessary files and directories is complete!')

class xg_analysis(pd.DataFrame):
    """Allows for visual analysis of xG values for all teams from English Premier League for current season"""
    def __init__(self,url="https://fbref.com/en/comps/9/schedule/Premier-League-Scores-and-Fixtures",
                 chrome_drive_loc=os.path.join(os.path.expanduser('~'),'xg_analysis/chromedriver'),
                 xpath='//*[@id="sched_11160_1_sh"]/div/ul/li[1]/div/ul/li[3]/button',
                 full_xpath='/html/body/div[3]/div[6]/div[2]/div[1]/div/ul/li[1]/div/ul/li[3]/button'):
        """Creates a pandas dataframe with team, score, date and xG values for all teams in current season.
        Uses selenium to download data from fbref website to achieve this"""

        download_path=os.path.join(os.path.expanduser('~'),'xg_analysis') # Specifying where Excel file from fbref should be downloaded to
        super(xg_analysis,self).__init__() # Initialising empty dataframe

        if 'sportsref_download.xls' in [val.name for val in os.scandir(download_path)]:
            fbref_dl_path = download_path + '/sportsref_download.xls'
            subprocess.run(['rm',f'{fbref_dl_path}'])

        self.url = url

        # Specifying necessary chromedriver options:
        chrome_options = webdriver.ChromeOptions()
        prefs = {'download.default_directory' : download_path}
        chrome_options.add_experimental_option('prefs', prefs)
        #chrome_options.add_argument('--headless') # All chromedriver activity be done in background # Appears not to work in headless mode after accounting for privacy message
        new_driver_path = ChromeDriverManager(path=download_path).install()
        subprocess.run(['mv',f'{new_driver_path}',f'{download_path}'])
        driver = webdriver.Chrome(service=webdriver.chrome.service.Service(executable_path=chrome_drive_loc),
                                  options=chrome_options) # Creates browser session
        driver.get(url) # Loads fbref url in browser session

        # Finding download link for dataset in fbref using HTML xpath
        self.xpath = xpath # More adaptable xpath than the full one below
        self.full_xpath = full_xpath # Would break if HTML chsnged only slightly

        # To get past data consent pop-up
        try:
            data_privacy = driver.find_elements(by=By.CLASS_NAME, value = 'qc-cmp2-summary-buttons')
            try:
                for val in data_privacy:
                    found = False
                    dp1 = val.find_elements(by=By.TAG_NAME, value = 'span')
                    for val_1 in dp1:
                        if val_1.text == 'DISAGREE':
                            found = True
                            driver.execute_script("arguments[0].click();", val_1)
                            break
                    if found:
                        break
            except:
                pass
        except:
            print('No consent confirmation')

        excel = driver.find_element(by=By.XPATH, value = xpath)
        driver.execute_script("arguments[0].click();", excel) # Explicitly specifying chromedriver to click on link. click method does not work

        driver.close() # closing the webdriver

        # Gathering data from excel file produced from clicking download link
        df = pd.DataFrame(pd.read_html(download_path+'/sportsref_download.xls',
                                             encoding='UTF-8')[0])
        df.dropna(subset=['Wk','Date','Home','xG','Score','xG.1','Away'],inplace=True)
        df.rename({'xG':'xG_Home','xG.1':'xG_Away'},axis=1,inplace=True)
        df['Date'] = pd.to_datetime(df['Date'])
        df.sort_values(by='Date',inplace=True)
        df.reset_index(inplace=True,drop=True)

        # Saving original dataframe for personal use or for method reverting changes back to original dataframe
        df.to_csv(download_path+'/xg_analysis.csv',index=False)

        super(xg_analysis,self).__init__(df) # Creating object as pandas dataframe so can use any pandas functions/methods desired on instance

    def choose_team(self,team=None):
        """Chooses team to conduct xG analysis on. Either by specifying team exactly, choosing from dropdown
           list of teams most likely meant from input, or choosing from dropdown list of all teams (default value)"""

        # Get list of all Premier League teams in current season and order them alphabetically
        all_teams = list(set(self.Home).intersection(self.Away))
        all_teams = sorted(all_teams)

        # Function used to create tkinter window with dropdown. Defined here to simplify and shorten code below
        def option_window(title_txt,val_list,question_asked=False):
            root = tk.Tk() # Initialise tkinter window
            root.title(title_txt) # Title window
            root.geometry('500x250') # Size window
            choice = tk.StringVar() # Initialise empty string that will become team choice later on
            dropdown = ttk.Combobox(root, values=val_list) # Add dropdown to window

            # Function to confirm team choice from dropdown list
            def confirm_val(*args):
                choice.set(dropdown.get()) # Assign choice string value initialised earlier dropdown list choice
                root.after(1, root.destroy()) # Close window after choice made

            # For use with dropdown with all teams (no 'team' argument specified)
            button = tk.Button(root,text='Confirm',command=confirm_val) # Adding 'Confirm' button to window
            dropdown.place(x=150,y=100) # Placing dropdown within window

            if question_asked: # Used when 'team' argument specified but not found in team list (Did you mean 'x' team?)

                # Specifying action taken when clicking 'No' button in window (when desired team not in dropdown created from most likely teams meant)
                def no_val(*args):
                    print(f"'{team}' not found. List of possible teams are as follows:\n")
                    for val in all_teams: # Print all possible teams with exact string values to help user find team
                        print(val)
                    root.after(1, root.destroy()) # Close window

                # Adding and placing 'No' button. Placing 'Confirm' button next to 'No' button
                button1 = tk.Button(root,text='No',command=no_val)
                button.place(x=170,y=125)
                button1.place(x=250,y=125)

            else:
                button.place(x=210,y=125) # Placing 'Confirm' button below dropdown when 'No' button not necessary


            root.mainloop() # Open window
            choice = choice.get() # Retrieve choice string value from dropdown list
            return choice

        # Generate dropdown list with all teams if 'team' argument is left as default/None
        if team == None:

            team_choice = option_window('Choose a team',all_teams)

            df = self[(self['Home']==team_choice) | (self['Away']==team_choice)]

        # If team specified and resulting dataframe is empty, looks to generate list of possibly meant choices
        else:

            team_choice = team
            df = self[(self['Home']==team_choice) | (self['Away']==team_choice)]
            if len(df) == 0:
                print('No football team match found. Generating list of options...')

                # Gathers common string matching metrics for search value against all teams
                def get_distances(search,target):
                    all_vals = []
                    for val in target:
                        metrics = {'name':val,'dam_lev':damerauLevenshtein(search,val),
                                   'jaro':jaro.jaro_metric(search,val),
                                   'jaro_wink':jaro.jaro_winkler_metric(search,val)}
                        all_vals.append(metrics)
                    return all_vals

                metric_vals = get_distances(team_choice,all_teams)
                # Limits on metric values for possible match have been set through examination of values
                filtered_list = list(filter(lambda x: team_choice in x['name'] or x['dam_lev'] > 0.5
                                            or x['jaro'] > 0.7
                                            or x['jaro_wink'] > 0.7,metric_vals))
                sorted_list = sorted(filtered_list,key = lambda x: (x['jaro'],x['jaro_wink'],x['dam_lev']),
                                     reverse=True)
                options = [val['name'] for val in sorted_list]

                # If options meeting limit criteria set above have been found, generates dropdown with options
                if len(options) > 0:

                    team_choice = option_window('No team found. Did you mean?',options,question_asked=True)

                    df = self[(self['Home']==team_choice) | (self['Away']==team_choice)]

                # If no options meeting limit criteria set above have been found, print team not found with possible choices
                else:
                    print(f"'{team}' not found. List of possible teams are as follows:\n")
                    for val in all_teams: # Print all possible teams with exact string values to help user find team
                        print(val)
                    return
        self.team_choice = team_choice # Add team_choice as object attribute (for use in other methods)
        df.reset_index(inplace=True,drop=True)
        super(xg_analysis,self).__init__(df) # Return updated dataframe

    def revert_choice(self):
        """Reverts back to original dataframe with data on all teams so that choice can be made again"""
        try: # Deletes team_choice attribute and changes instance to original dataframe
            del self.team_choice
            df = pd.read_csv(os.path.join(os.path.expanduser('~'),'xg_analysis/xg_analysis.csv'))
        except AttributeError: # team_choice attribute already removed
            print('DataFrame already reverted to original')
            return
        except FileNotFoundError: # CSV file with original dataframe data has been removed
            print('Original DataFrame saved when initialising instance has been deleted.')
            print('Instance will have to be re-initialised in order to revert to original DataFrame')
            return
        super(xg_analysis,self).__init__(df) # Return updated dataframe

    def _get_columns(self):
        """Generates a variety of columns that are used for visual anaysis of a team's xG values"""
        xgf = []
        xga = []
        side = []
        result = []
        wdl = []
        for i in range(len(self)):
            scores = list(test['Score'])[i].split('–')
            scores = [int(val) for val in scores] # Get list of both side's score for each match
            # Add xG for and against values depending on whether playing at home or away
            if list(self['Home'])[i] == self.team_choice:
                xgf.append(list(self['xG_Home'])[i])
                xga.append(list(self['xG_Away'])[i])
                side.append('Home')
                # Add result (win, draw or loss) value using scores list
                if scores[0] > scores[1]:
                    wdl.append('W')
                elif scores[0] == scores[1]:
                    wdl.append('D')
                elif scores[0] < scores[1]:
                    wdl.append('L')
            elif list(self['Away'])[i] == self.team_choice:
                xgf.append(list(self['xG_Away'])[i])
                xga.append(list(self['xG_Home'])[i])
                side.append('Away')
                if scores[0] > scores[1]:
                    wdl.append('L')
                elif scores[0] == scores[1]:
                    wdl.append('D')
                elif scores[0] < scores[1]:
                    wdl.append('W')
            # Add complete result including team names and scoreline for later use creating graphs
            result.append(list(self['Home'])[i]+' '+list(self['Score'])[i]+' '+list(self['Away'])[i])
        # Add columns to dataframe from lists populated in for loop above
        self['Matchday'] = [i+1 for i in range(len(list(self.index)))]
        self['xGf'] = xgf
        self['xGa'] = xga
        self['Side'] = side
        self['Result'] = result
        self['Win/Draw/Loss'] = wdl

    def _initialise_graph(self,line_cols,line_names,y_axis_vars,hover_data,
                          diff,ytitle,title):
        """Initialises graph for use in xg_graph and xg_graph_diff methods. Creates two different types of graphs
           depending on whether graph is analysing difference (1 line) or both xG for and against (2 lines)"""
        fig = px.line(self, x="Matchday", y=y_axis_vars, hover_data=hover_data, title=title) # Create line graph
        fig['data'][0]['line']['color'] = line_cols[0] # Specify 1st line colour
        fig['data'][0]['name'] = line_names[0] # Specify 1st line name (shown in key)
        # Add specs for other line if graph is not analysing difference and alter info included when hovering over points on graph
        if not diff:
            fig['data'][1]['line']['color'] = line_cols[1] # Specify 2nd line colour
            fig['data'][1]['name'] = line_names[1] # Specify 2nd line name (shown in key)
            # Specify what is shown when hovering over points on graph
            fig['data'][0]['hovertemplate'] = 'Variable=xGF<br>Matchday=%{x}<br>Value=%{y}<br>Side=%{customdata[0]}<br>W/D/L=%{customdata[1]}<br>Result=%{customdata[2]}<br>xGf=%{customdata[3]}<br>xGa=%{customdata[4]}<extra></extra>'
            fig['data'][1]['hovertemplate'] = 'Variable=xGA<br>Matchday=%{x}<br>Value=%{y}<br>Side=%{customdata[0]}<br>W/D/L=%{customdata[1]}<br>Result=%{customdata[2]}<br>xGf=%{customdata[3]}<br>xGa=%{customdata[4]}<extra></extra>'
        else:
            fig['data'][0]['hovertemplate'] = 'Variable=xG_diff<br>Matchday=%{x}<br>Value=%{y}<br>Side=%{customdata[0]}<br>W/D/L=%{customdata[1]}<br>Result=%{customdata[2]}<br>xGf=%{customdata[3]}<br>xGa=%{customdata[4]}<extra></extra>'
            fig.add_hline(y=0) # Add 0 line to graph for help analysing difference between xG for and against

        # Update layout with specific axes and background colours, alongside content and placement of title
        fig.update_layout(xaxis=dict(showline=True,linecolor='rgb(153, 153, 153)',linewidth=2),
                  yaxis=dict(showline=True,linecolor='rgb(153, 153, 153)',linewidth=2),
                  showlegend=True,plot_bgcolor='white',hoverlabel=dict(bgcolor="white"),
                  yaxis_title=ytitle,title_x=0.5)
        fig.update_traces(mode='markers+lines')

        return fig

    def _calculate_averages(self,avg_length):
        """Calculates averages of xG for and against values over a specified number of matches"""
        xgf_avg = []
        xga_avg = []
        for i in range(len(self)):
            xgf = []
            xga = []
            for j in range(i-avg_length+1,i+1):
                if j < 0: # Ensure negative indexing is not carried out (collecting values near end of list accidentally)
                    continue
                xgf.append(list(self['xGf'])[j])
                xga.append(list(self['xGa'])[j])
            xgf_avg.append(sum(xgf)/len(xgf))
            xga_avg.append(sum(xga)/len(xga))
        xgf_col = 'xGf_avg{num}'.format(num=str(avg_length)) # Create string value of new column name to added for average xG for
        xga_col = 'xGa_avg{num}'.format(num=str(avg_length)) # Create string value of new column name to added for average xG for
        return (xgf_col,xga_col,xgf_avg,xga_avg)

    def xg_graph(self,avg_length,team_choice=None):
        """Produces a graph showing a chosen team's average (over a specified number of matches) xG values
           for and against over a season"""
        if 'team_choice' not in dir(self): # Call choose_team method if no team has been chosen to conduct analysis on
            print('Team not chosen. choose_team method called')
            self.choose_team()
        elif team_choice is not None: # Allows team_choice to be specified in this function instead of using choose_team method
            self.revert_choice()
            self.choose_team(team_choice)
        self._get_columns() # Call _get_columns method to add columns used in graph to dataframe
        for val in list(self.columns):
            if val.startswith('xGf_avg') or val.startswith('xGa_avg'):
                self.drop([val],axis=1,inplace=True) # Removes existing xG average columns to then replace them with new columns
        avg_vals = self._calculate_averages(avg_length)
        self[avg_vals[0]] = avg_vals[2] # Add new xG for average column
        self[avg_vals[1]] = avg_vals[3] # Add new xG against average column
        # Specify different axis and title labels depending on whether values are averaged (avg_length>1) or not (avg_length=1)
        if avg_length == 1:
            figure = self._initialise_graph(['#26ab40','#EF553B'],['xGf','xGa'],
                                            ['xGf_avg{num}'.format(num=str(avg_length)),
                                             'xGa_avg{num}'.format(num=str(avg_length))],
                                            ['Side','Win/Draw/Loss','Result','xGf','xGa'],False,
                                            'xGF/xGA',
                                            '{team} xG For and Against Plot'.format(team=self.team_choice))
        else:
            figure = self._initialise_graph(['#26ab40','#EF553B'],['xGf','xGa'],
                                            ['xGf_avg{num}'.format(num=str(avg_length)),
                                             'xGa_avg{num}'.format(num=str(avg_length))],
                                            ['Side','Win/Draw/Loss','Result','xGf','xGa'],False,
                                            'xGF/xGA {num} game averages'.format(num=str(avg_length)),
                                            '{team} xG For and Against Average Over {num} Games Plot'.format(team=self.team_choice,num=avg_length))
        figure.show()

    def xg_graph_diff(self,avg_length,team_choice=None):
        """Produces a graph showing a chosen team's difference in average (over a specified number of matches)
           xG values for and against over a season"""
        if 'team_choice' not in dir(self): # Call choose_team method if no team has been chosen to conduct analysis on
            print('Team not chosen. choose_team method called')
            self.choose_team()
        elif team_choice is not None: # Allows team_choice to be specified in this function instead of using choose_team method
            self.revert_choice()
            self.choose_team(team_choice)
        self._get_columns() # Call _get_columns method to add columns used in graph to dataframe
        for val in list(self.columns):
            if val.startswith('xGf_avg') or val.startswith('xGa_avg') or val.startswith('xG_diff_avg'):
                self.drop([val],axis=1,inplace=True) # Removes existing xG average columns to then replace them with new column
        avg_vals = self._calculate_averages(avg_length)
        diff_col = 'xG_diff_avg{num}'.format(num=avg_length)
        diff_avgs = [avg_vals[2][i] - avg_vals[3][i] for i in range(len(avg_vals[2]))] # Calculating difference between xG average for and against values
        self[diff_col] = diff_avgs # Add new xG average difference column
        # Specify different axis and title labels depending on whether values are averaged (avg_length>1) or not (avg_length=1)
        if avg_length == 1:
            figure = self._initialise_graph(['#636efa'],['xG diff'],
                                            ['xG_diff_avg{num}'.format(num=str(avg_length))],
                                            ['Side','Win/Draw/Loss','Result','xGf','xGa'],True,
                                            'xGF/xGA difference',
                                            '{team} xG Difference Plot'.format(team=self.team_choice))
        else:
            figure = self._initialise_graph(['#636efa'],['xG diff'],
                                            ['xG_diff_avg{num}'.format(num=str(avg_length))],
                                            ['Side','Win/Draw/Loss','Result','xGf','xGa'],True,
                                            'xGF/xGA difference {num} game averages'.format(num=str(avg_length)),
                                            '{team} xG Difference Average Over {num} Games Plot'.format(team=self.team_choice,num=avg_length))
        figure.show()
