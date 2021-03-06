# Strava Airflow pipeline

Having discovered Apache Airflow, I wanted to have a go at creating a pipeline of my own. I chose this example because I have recently started running again and want to easily analyse how/in what areas I am improving run-by-run. This data collection helps to do this.

This flow allows its user to grab data from their recorded Strava exercises and store them for analysis, using the Strava API (https://developers.strava.com/docs/reference/). An update allows the user to gather weather data for analysis and comparison against run data.

The flow's tasks are as follows:

- __get_access_token__: Retrieves the necessary information to be able to access personal data on Strava (authorization token must already have been created).

- __trigger_other_tasks__: Looks for id values for any new runs (those that have not yet been added to storage), if the GET request response for a new access token is successful (i.e., status_code = 200). Future tasks are skipped if there is no new data.

- __gather_detailed_info__: Takes id values for any new runs and gathers detailed data from each run and weather data for the day and time of the run.

- __append_run_data__: If new data is found, it is then appended to the existing JSON-formatted data.

I have scheduled the DAG to run every day at 13:00 and 20:00 (local time) to ensure data is gathered relatively soon after it is created.
