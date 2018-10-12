import requests
import pandas
import math
from requests.auth import HTTPBasicAuth
from bs4 import BeautifulSoup
import time
import os

"""
This script is used for get Jira items Plan time, and export result to csv file.
Run Steps:
1. Download and install Python V3.4.4 from '\\zhuradnasw02\Store\spark\devenv'
2. Download package pandas-0.22.0-cp34-cp34m-win_amd64.whl from '\\zhuradnasw02\Store\spark\devenv'
   Pls make sure the pandas version match with your python version(here both v3.4)
3. run command in CMD mode: 
    > pip install %path%/pandas-0.22.0-cp34-cp34m-win_amd64.whl
4. run this script in CMD mode, pls make sure the path exists, and you have permission to create new file: 
    > python %path%/get_time_to_csv.py
5. the csv file will saved into %csv_path%
"""

sprint_id = os.environ["SPRINT_ID"]
jira_user = os.environ["JIRA_USER"]
jira_pwd = os.environ["JIRA_PWD"]
csv_path = "{0}\SprintPlan{1}_Build{2}.csv".format(os.environ["WORKSPACE"], sprint_id, os.environ["B"])


def get_basic_auth():
    global jira_user, jira_pwd
    # get all item back in given TIC Sprint ID
    if not jira_user:
        jira_user = "aaron.xu@quest.com"
    if not jira_pwd:
        jira_pwd = "Quest@06"
    return HTTPBasicAuth(jira_user, jira_pwd)


def get_tic_individual_back_from_wiki():
    print("Read tic_individual page html back from wiki ...")
    basic_auth = get_basic_auth()
    url = "https://wiki.labs.quest.com/display/toadcloud/TIC+Individual+Capacity+By+Sprint"
    tic_individual_html = requests.request('Get', url, auth=basic_auth, timeout=120)
    return tic_individual_html.content


def read_table_body_from_html_content(tic_individual_html):
    global sprint_id
    print("Filter current sprint {0} team capacity time".format(sprint_id))
    soup = BeautifulSoup(tic_individual_html, "html.parser")
    table_id = "TICIndividualCapacityBySprint-TICSprint{0}Sprint{0}".format(sprint_id)
    sprint_title = soup.find(id=table_id)
    if sprint_title:
        table_body = sprint_title.find_next('tbody').contents
        return table_body


def generic_team_capacity_to_dict(table_body):
    print("Save team capacity time into Dict")
    team_capacity = dict()
    for row in table_body:
        if row('p'):
            dict_key = row('td')[0].string if row('td')[0].string != 'Jimmy' else 'Zhiming'
            team_capacity[dict_key] = [row('td')[2].string, row('td')[4].string]
    return team_capacity


def get_sprint_all_items():
    global sprint_id, jira_user, jira_pwd
    print("Get all JIRA items back in TIC Sprint {0}...".format(sprint_id))
    basic_auth = get_basic_auth()
    url = "https://jira.labs.quest.com/rest/api/2/search?jql=sprint='TIC Sprint {0}'&maxResults=500".format(sprint_id)
    all_items = requests.request('Get', url, auth=basic_auth).json()['issues']
    return all_items


def filter_items_property(all_items):
    """
        # filter jira item properties, just keep the property what we need
        # NOTE: currently, we read remaining time for each item, as it may comes from last sprint
    """
    print("Filter all items properties")
    all_tasks = list()
    for item in all_items:
        if item['fields']['status']['name'].lower() != 'closed' and item['fields']['summary'].find("Unknown Work") < 0:
            # if item already closed, or it's unplan unknown work item, then ignore these items
            dic_property = dict()
            dic_property['key'] = item['key']
            dic_property['parent_key'] = item['fields']['parent']['key'] if 'parent' in item['fields'] else ''
            dic_property['assign'] = item['fields']['assignee']['displayName'].partition('(')[0] if item['fields']['assignee'] else 'Unassigned'
            dic_property['type'] = item['fields']['issuetype']['name']
            dic_property['remaining'] = int(item['fields']['timeestimate'])/3600 if item['fields']['timeestimate'] else 0
            dic_property["summary"] = item['fields']['summary']
            dic_property["sub_tasks"] = item['fields']['subtasks']
            # dic_property['target_completion'] = item['fields']['customfield_19015-val'] if 'customfield_19015-val' in item['fields'] else ''
            all_tasks.append(dic_property)
    return all_tasks


def generic_file_column(tasks):
    header = set()
    for item in tasks:
        if item['summary'].find('UnplannedUnknown Work') == -1:
            item_key = item['parent_key'] if item['parent_key'] else item['key']
            header.add(item_key)
    sort_header = sorted(list(header))
    sort_header.insert(0, 'MaximumCapacity')
    sort_header.insert(1, 'EstimatedCapacity')
    sort_header.insert(2, 'UsedTime')
    return sort_header


def generic_file_index(tasks):
    members = set()
    for task in tasks:
        members.add(task['assign'])
    index = sorted(list(members))
    return index


def apply_format(value):
    # default value are display as hours, format value to day.hour
    dd = value // 8
    hh = value % 8
    if dd > 0 and hh > 0:
        return "{0}d {1}h".format(int(dd), int(hh))
    elif dd > 0:
        return "{0}d".format(int(dd))
    elif hh > 0:
        return "{0}h".format(int(hh))
    else:
        return ''


def format_work_time_to_day_hour():
    for index in range(len(name_index)):
        for column in range(len(headers)):
            df.iloc[index, column] = apply_format(df.iloc[index, column])


def read_item_info_into_data_frame(items):
    print("Read items plan time into data frame")
    for item in items:
        if len(item['sub_tasks']) > 0:
            # if item with sub tasks don't need to count estimated time, just count sub-task's estimated time
            continue
        if item['parent_key']:
            # exists parent item, so it's bug, sub-task..
            # in one story, there may be multiple sub tasks for one user
            if math.isnan(df.at[item['assign'], item['parent_key']]):
                df.at[item['assign'], item['parent_key']] = item['remaining']
            else:
                df.at[item['assign'], item['parent_key']] += item['remaining']
        else:
            # it's task...
            df.at[item['assign'], item['key']] = item['remaining']
    df['UsedTime'] = df.apply(lambda x: x.sum(), axis='columns')


def read_team_capacity_into_data_frame(team_capacity):
    global name_index
    print("Read wiki capacity time into data frame")
    for jira_name in name_index:
        for wiki_name in team_capacity.keys():
            if wiki_name.lower() in jira_name.lower():
                df.at[jira_name, "MaximumCapacity"] = float(team_capacity[wiki_name][0]) * 8
                df.at[jira_name, "EstimatedCapacity"] = float(team_capacity[wiki_name][1]) * 8
            continue


def write_data_frame_to_csv_file():
    global csv_path
    try:
        print("Begin write data frame into local csv file.")
        df.to_csv(csv_path)
    except PermissionError:
        new_path = csv_path.partition('.csv')[0] + '_' + time.strftime("%Y%m%d%H%M%S") + csv_path.partition('.csv')[1]
        print("Target file '{0}' may already opened. \nDone. Save csv to new path: {1}.".format(csv_path, new_path))
        df.to_csv(new_path)
    else:
        print("\nDone. File has been saved into: {0}".format(csv_path))


if __name__ == "__main__":
    capacity_dict = generic_team_capacity_to_dict(read_table_body_from_html_content(get_tic_individual_back_from_wiki()))
    items_info = filter_items_property(get_sprint_all_items())
    headers = generic_file_column(items_info)
    name_index = generic_file_index(items_info)
    df = pandas.DataFrame(columns=headers, index=name_index)
    read_item_info_into_data_frame(items_info)
    read_team_capacity_into_data_frame(capacity_dict)
    format_work_time_to_day_hour()
    write_data_frame_to_csv_file()















