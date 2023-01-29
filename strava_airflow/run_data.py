import requests
import json
import time
import datetime
import re
import sys
from airflow import DAG
from airflow.operators.python import PythonOperator, ShortCircuitOperator

def get_access_token():

    with open('/Users/jamesmead/Run Data/credentials.json','r') as fid:
        creds = json.load(fid)

    oauth_url = 'https://www.strava.com/oauth/token'

    data = {
       'client_id': creds['client_id'],
       'client_secret': creds['client_secret'],
       'refresh_token': creds['refresh_token'],
       'grant_type': 'refresh_token'}

    r = requests.post(oauth_url, data=data)
    creds['status_code'] = r.status_code
    r = r.json()
    creds['access_token'] = r['access_token']

    with open('/Users/jamesmead/Run Data/credentials.json','w') as fid:
        json.dump(creds,fid)

def clean_file():

    with open('/Users/jamesmead/Run Data/run_data.json','r') as fid:
        run_data = json.load(fid)

    if len(run_data) == 0:
        return

    for i in range(len(run_data)):
        if i >= len(run_data):
            break
        else:
            run_data_comp = run_data[:]
            run_data_comp.pop(i)
            if run_data[i] in run_data_comp:
                run_data.pop(i)

    run_data = sorted(run_data, key = lambda val:datetime.datetime.strptime(val['start_date'], "%Y-%m-%dT%H:%M:%SZ"))

    with open('/Users/jamesmead/Run Data/credentials.json','r') as fid:
        creds = json.load(fid)

    if creds['status_code'] == 200:
        headers = {"Authorization": "Bearer {}".format(creds['access_token'])}
        break_num = 0
        for i in range(len(run_data)):
            if break_num >= 25:
                break
            if re.search('\d+',run_data[i]['name']) == None:
                url_updt = 'https://www.strava.com/api/v3/activities/{}'.format(run_data[i]['id'])
                data_updt = {'name':'FJ - {}'.format(i+1)}
                r_updt = requests.put(url_updt,headers=headers,data=data_updt)
                break_num = break_num + 1
                if r_updt.status_code == 200:
                    run_data[i]['name'] = data_updt['name']
                else:
                    sys.exit(1)
            elif re.search('\d+',run_data[i]['name']).group() != str(i+1):
                url_updt = 'https://www.strava.com/api/v3/activities/{}'.format(run_data[i]['id'])
                data_updt = {'name':re.sub('\d+','{}',run_data[i]['name']).format(i+1)}
                r_updt = requests.put(url_updt,headers=headers,data=data_updt)
                break_num = break_num + 1
                if r_updt.status_code == 200:
                    run_data[i]['name'] = data_updt['name']
                else:
                    sys.exit(1)

    else:
        sys.exit(1)

    with open('/Users/jamesmead/Run Data/run_data.json','w') as fid:
        json.dump(run_data,fid)

def trigger_other_tasks(ti):

    with open('/Users/jamesmead/Run Data/credentials.json','r') as fid:
        creds = json.load(fid)

    if creds['status_code'] == 200:
        start_date_dt = datetime.datetime.strptime(creds['search_date'], "%Y-%m-%dT%H:%M:%SZ")
        start_date_tuple = start_date_dt.timetuple()
        start_date_unix = int(time.mktime(start_date_tuple))

        # store URL for activities endpoint
        base_url = "https://www.strava.com/api/v3/"
        endpoint = "athlete/activities"
        url = base_url + endpoint
        # define headers and parameters for request
        headers = {"Authorization": "Bearer {}".format(creds['access_token'])}
        params = {'after':start_date_unix}
        # make GET request to Strava API
        req = requests.get(url, headers = headers,params=params)
        if req.status_code == 200:
            req = req.json()
            if len(req) == 0:
                return False
            else:
                act_ids = [req[i]['id'] for i in range(len(req))]
                creds['search_date'] = req[-1]['start_date_local']
                with open('/Users/jamesmead/Run Data/credentials.json','w') as fid:
                    json.dump(creds,fid)
                ti.xcom_push(key='id_info', value=act_ids)
                return True
        else:
            return False

    else:
        return False

def gather_detailed_info(ti):

    with open('/Users/jamesmead/Run Data/credentials.json','r') as fid:
        creds = json.load(fid)

    act_ids = ti.xcom_pull(key='id_info')

    new_run_data = []
    for val in act_ids:
        base_url = "https://www.strava.com/api/v3/"
        endpoint = "activities/{}".format(val)
        url = base_url + endpoint
        # define headers and parameters for request
        headers = {"Authorization": "Bearer {}".format(creds['access_token'])}
        params = {'include_all_efforts':True}
        req = requests.get(url, headers = headers,params=params)
        if req.status_code == 200:
            req = req.json()
            cols = ['name','distance','moving_time','elapsed_time','total_elevation_gain','id','start_date',
                    'start_date_local','summary_polyline','average_speed','max_speed','elev_high',
                    'elev_low','description','perceived_exertion','splits_metric','best_efforts','similar_activities']
            run = {}
            for val in cols:
                if val in req.keys():
                    if val == 'summary_polyline':
                        run['polyline'] = req['map'][val]
                    else:
                        run[val] = req[val]
            try:
                weather_url = "https://api.openweathermap.org/data/3.0/onecall/timemachine"
                weather_params = {'lat':'56.15372056606176','lon':'-3.8009364730092274',
                          'dt':str(int(time.mktime(datetime.datetime.strptime(run['start_date_local'],"%Y-%m-%dT%H:%M:%SZ").timetuple()))),
                          'units':'metric',
                          'appid':creds['weather_api_key']}
                weather_req = requests.get(weather_url, params=weather_params)
                weather_req = weather_req.json()
            except:
                raise Exception('Weather data not collected')
            weather_cols = ['temp','feels_like','humidity','wind_speed','wind_deg']
            for val in weather_cols:
                run[val] = weather_req['data'][0][val]
            new_run_data.append(run)
            with open('/Users/jamesmead/Run Data/run_data_add.json','w') as fid:
                fid.write('')
            with open('/Users/jamesmead/Run Data/run_data_add.json','w') as fid:
                json.dump(new_run_data,fid)
        else:
            raise Exception('Response unsuccessful')

def append_run_data(ti):

    with open('/Users/jamesmead/Run Data/run_data.json','r') as fid:
        run_data = json.load(fid)

    with open('/Users/jamesmead/Run Data/run_data_add.json','r') as fid:
        new_run_data = json.load(fid)

    for val in new_run_data:
        if val not in run_data:
            run_data.append(val)

    with open('/Users/jamesmead/Run Data/run_data.json','w') as fid:
        json.dump(run_data,fid)

dag_args = {
'email': ['jamesamead5@gmail.com'],
'email_on_failure': True
}

dag = DAG('Strava_data_grab', default_args = dag_args, description= 'DAG to search for most recent run data from Strava and add to existing data if new',
schedule_interval=None,#'0 12,19 * * *',
start_date=datetime.datetime(2022, 6, 5), catchup=False)

retrieve_access_token = PythonOperator(task_id='access_token_task', python_callable=get_access_token, dag=dag)

start_clean_up = PythonOperator(task_id='START_clean_data', python_callable=clean_file, dag=dag)

continue_tasks = ShortCircuitOperator(task_id='trigger_future_tasks',python_callable=trigger_other_tasks,dag=dag)

get_data = PythonOperator(task_id='get_detailed_info_task',python_callable=gather_detailed_info, dag=dag)

add_run_data = PythonOperator(task_id='add_run_data_task', python_callable=append_run_data, dag=dag)

end_clean_up = PythonOperator(task_id='END_clean_data', python_callable=clean_file, dag=dag)

retrieve_access_token >> start_clean_up >> continue_tasks >> get_data >> add_run_data >> end_clean_up
