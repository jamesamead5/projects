# xg_analysis

I was not very familiar with how classes and methods worked so I decided to have a go at creating one myself. I chose this example because I am passionate about football analytics and have written a paper on the use of xG within football.

 This class allows users to easily visualise expected goals (xG) values for all teams within the Big 5 leagues (English Premier League, Spanish La Liga, German Bundesliga, Italian Serie A and French Ligue 1) for any season from 2017-2018 (no xG data is available before this season), using data gathered from fbref (https://fbref.com/en/).

Since xG data on fbref is accessible through downloading an Excel file on their Scores and Fixtures page, the selenium package is used to open a window on this page and click on the widget which downloads the Excel file. The data within this Excel file is then used to create a pandas dataframe containing the necessary columns for analysis. This completes initialisation.

After first working on this project, fbref have both added an inital pop-up for accept or deny cookie use and, seemingly in response to bots accessing their website, have added reCAPTCHA authentication when unusual behaviour is detected. The former problem has been resolved by adding logic to seek out the 'Disagree' button and click it (unfortunately having the unintended effect of not being able to run the selenium window in the background). Whilst not resolved entirely, the occurence of the latter problem has been severely reduced by adding time.sleep() commands to appear more human-like in the bot's actions. This naturally reduces the speed at which the data can be accessed but is an easy fix to the existing problem.

The class methods are as follows:

- __choose_team__: Chooses team to conduct xG analysis on. Either by specifying team exactly, choosing from dropdown list of teams most likely meant from input, or choosing from dropdown list of all teams (default value) (uses tkinter package)

- __revert_choice__: Reverts back to original dataframe with data on all teams so that choice can be made again by deleting team_choice attribute and reinitialising object as original dataframe

- __xg_graph__: Leverages several hidden functions to produces a graph showing a chosen team's average (over a specified number of matches) xG values for and against over a season

- __xg_graph_diff__: Similar to the previous method but produces a graph showing a chosen team's difference in average (over a specified number of matches) xG values for and against over a season
