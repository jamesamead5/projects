# xg_analysis

I was not very familiar with how classes and methods worked so I decided to have a go at creating one myself. I chose this example because I am passionate about football analytics and have written a paper on the use of xG within football.

 This class allows users to easily visualise expected goals (xG) values for Premier League teams, using data gathered from fbref (https://fbref.com/en/).

Since xG data on fbref is accessible through downloading an Excel file on their Scores and Fixtures page, the selenium package is used to open a window on this page and click on the widget which downloads the Excel file. The data within this Excel file is then used to create a pandas dataframe containing the necessary columns for analysis. This completes initialisation.

The class methods are as follows:

- __choose_team__: Chooses team to conduct xG analysis on. Either by specifying team exactly, choosing from dropdown list of teams most likely meant from input, or choosing from dropdown list of all teams (default value) (uses tkinter package)

- __revert_choice__: Reverts back to original dataframe with data on all teams so that choice can be made again by deleting team_choice attribute and reinitialising object as original dataframe

- __xg_graph__: Leverages several hidden functions to produces a graph showing a chosen team's average (over a specified number of matches) xG values for and against over a season

- __xg_graph_diff__: Similar to the previous method but produces a graph showing a chosen team's difference in average (over a specified number of matches) xG values for and against over a season
