import os
import requests
from requests.auth import HTTPBasicAuth
from bs4 import BeautifulSoup
from prettytable import PrettyTable
import webcommon

sprint_id = int(os.environ["SPRINT_ID"])
jira_user = os.environ["JIRA_USER"]
jira_pwd = os.environ["JIRA_PWD"]
csv_path = "{0}\SprintPlan{1}_Build{2}.csv".format(os.environ["WORKSPACE"], sprint_id, os.environ["BUILD_NUMBER"])

# sprint_id = 54
# jira_user = 'aaron.xu@quest.com'
# jira_pwd = ''
# csv_path = "{0}\SprintPlan{1}.csv".format('C:\python34', sprint_id)

sprint_number = None


def get_basic_auth():
    global jira_user, jira_pwd
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


def generate_team_capacity_to_dict(table_body):
    print("Save team capacity time into Dict")
    team_capacity = dict()
    for row in table_body:
        if row('p'):
            dict_key = row('td')[0].string if row('td')[0].string != 'Jimmy' else 'Zhiming'
            team_capacity[dict_key] = [row('td')[2].string, row('td')[4].string]
    return team_capacity


def get_team_max_capacity(dict_capacity):
    team_max_capacity = 0
    for item in dict_capacity:
        team_max_capacity += float(dict_capacity[item][0])
    return team_max_capacity


def get_team_estimated_capacity(dict_capacity):
    team_estimated_capacity = 0
    for item in dict_capacity:
        team_estimated_capacity += float(dict_capacity[item][1])
    return team_estimated_capacity


def login_jira():
    if not webcommon.get_object_by_id("header-details-user-fullname", 1):
        print("Login in to jira ...")
        webcommon.get_object_by_id("login-form", 60)
        webcommon.get_object_by_id("login-form-username").send_keys(jira_user)
        webcommon.get_object_by_id("login-form-password").send_keys(jira_pwd)
        webcommon.get_object_by_id("login-form-remember-me").click()
        webcommon.get_object_by_id("login-form", 15).submit()
        webcommon.get_object_by_id("login-form", -15)


def get_tic_scrum_dashboard_back():
    print("Read tic scrum dashboard page html back from wiki ...")
    basic_auth = get_basic_auth()
    url = "https://wiki.labs.quest.com/display/toadcloud/TIC+Scrum+Dashboard"
    tic_scrum_dashboard = requests.request('Get', url, auth=basic_auth, timeout=120)
    return tic_scrum_dashboard.content


def get_jira_page_source_back(url):
    print("Open page {0}".format(url))
    webcommon.get_driver().get(url)
    login_jira()
    webcommon.get_object_by_css("table", 60)
    page_source = webcommon.get_driver().page_source
    return page_source


def get_last_sprint_value_from_tic_scrum_dashboard(tic_scrum_dashboard, row_index, line_index):
    soup = BeautifulSoup(tic_scrum_dashboard, "html.parser")
    row = soup.find_all("a", string=sprint_id-1)[row_index]
    line = row.find_parent('td').find_parent('tr').find_all("td")[line_index].string
    return int(line.partition("/")[0].partition('(')[2])


def generate_last_sprint_values(tic_scrum_dashboard):
    last_total_ave_unplan_work = get_last_sprint_value_from_tic_scrum_dashboard(tic_scrum_dashboard, 1, 4)
    last_total_ave_sp_completed = get_last_sprint_value_from_tic_scrum_dashboard(tic_scrum_dashboard, 2, 3)
    last_total_ave_percent_sp_completed = get_last_sprint_value_from_tic_scrum_dashboard(tic_scrum_dashboard, 2, 5)
    last_total_ave_completed = get_last_sprint_value_from_tic_scrum_dashboard(tic_scrum_dashboard, 3, 5)
    return [last_total_ave_unplan_work,
            last_total_ave_sp_completed,
            last_total_ave_percent_sp_completed,
            last_total_ave_completed]


def generate_plan_metrics_table_value(dict_capacity, base_value):
    print("\nTable Planning Metrics Values:")
    max_capacity = get_team_max_capacity(dict_capacity)
    estimated_capacity = get_team_estimated_capacity(dict_capacity)
    est_work = int(round((max_capacity - estimated_capacity)/max_capacity, 2)*100)
    est_work_text = '{0}%'.format(est_work)
    ave_work_value = round((base_value[0] + est_work)/(sprint_id - 1), 1)
    ave_work_text = '{0}%({1}/{2})'.format(ave_work_value, base_value[0]+est_work, sprint_id-1)
    x = PrettyTable()
    x.field_names = ['Sprint', "Maximum Capacity", "Estimated Capacity", "Est % of Unp/Unk Work",
                     "Ave % of Unp/Unk Work", "Committed Time", "Comments"]
    x.add_row([sprint_id, max_capacity, estimated_capacity, est_work_text, ave_work_text, '', ''])
    print(x)
    burndown_chart_url = "https://jira.labs.quest.com/secure/RapidBoard.jspa?rapidView=1785&view=reporting&chart=burndownChart&sprint={0}".format(sprint_number)
    print("Pls get 'Commited Time' from here: {0}".format(burndown_chart_url))


def get_sp_value_from_jira(velocity_chart_html):
    global sprint_number
    soup = BeautifulSoup(velocity_chart_html, "html.parser")
    sprint_cell = soup.find("a", string="TIC Sprint {0}".format(sprint_id))
    commitment = int(sprint_cell.find_parent('td').find_parent('tr').find_all("td")[1].string)
    completed = int(sprint_cell.find_parent('td').find_parent('tr').find_all("td")[2].string)
    sprint_number = sprint_cell.attrs['href'].split("=")[-1]
    return [commitment, completed]


def get_issue_completion_metrics_from_jira(sprint_report_html):
    global sprint_number
    committed = 0
    added = 0
    punted = 0
    completed = 0
    soup = BeautifulSoup(sprint_report_html, "html.parser")
    completed_h4 = soup.find("h4", string='Completed Issues')
    if completed_h4:
        rows = completed_h4.find_parent('div').find_parent('div').next_sibling.find_all('tr')
        for row in rows[1:]:
            if row.find('td').next_sibling.text.find("Unknown Work") > 0:
                continue
            if row.find('td'):
                completed += 1
                if row.find('td').text.find("*") > 0:
                    added += 1
                else:
                    committed += 1

    not_completed_h4 = soup.find("h4", string='Issues Not Completed')
    if not_completed_h4:
        rows = not_completed_h4.find_parent('div').find_parent('div').next_sibling.find_all('tr')
        for row in rows[1:]:
            if row.find('td'):
                punted += 1
                if row.find('td').text.find("*") > 0:
                    added += 1
                else:
                    committed += 1
    outside_completed_h4 = soup.find("h4", string='Issues completed outside of this sprint')
    if outside_completed_h4:
        rows = outside_completed_h4.find_parent('div').find_parent('div').next_sibling.find_all('tr')
        for row in rows[1:]:
            if row.find('td'):
                completed += 1
                if row.find('td').text.find("*") > 0:
                    added += 1
                else:
                    committed += 1
    remove_sprint_h4 = soup.find("h4", string='Issues Removed From Sprint')
    if remove_sprint_h4:
        rows = remove_sprint_h4.find_parent('div').find_parent('div').next_sibling.find_all('tr')
        for row in rows[1:]:
            if row.find('td'):
                punted += 1
                if row.find('td').text.find("*") > 0:
                    added += 1
                else:
                    committed += 1
    return [committed, added, punted, completed]


def generate_velocity_metrics_table_value(jira_sp, base_value):
    print("\nTable Velocity Metrics Values:")
    commitment = jira_sp[0]
    completed = jira_sp[1]
    ave_sp_completed = round((base_value[1]+completed)/(sprint_id-1), 1)
    ave_sp_completed_text = '{0}%({1}/{2})'.format(ave_sp_completed, base_value[1]+completed, sprint_id-1)
    percent_sp_completed = int(round(completed/commitment, 2)*100)
    percent_sp_completed_text = "{0}%".format(percent_sp_completed)
    ave_percent_sp_completed = round((base_value[2]+percent_sp_completed)/(sprint_id-1), 1)
    ave_percent_sp_completed_text = '{0}%({1}/{2})'.format(ave_percent_sp_completed,
                                                           base_value[2]+percent_sp_completed,
                                                           sprint_id-1)
    x = PrettyTable()
    x.field_names = ['Sprint', "SP Commitment", "SP Completed", "Ave SP Completed",
                     "% SP Completed", "Ave % SP Completed", "Comments"]
    x.add_row([sprint_id, commitment, completed, ave_sp_completed_text, percent_sp_completed_text,
               ave_percent_sp_completed_text, ''])
    print(x)


def generate_issue_completion_metrics_table_value(jira_commit, base_value):
    print("\nTable Issue Completion Metrics Values:")
    ave_completed = round((base_value[3] + jira_commit[3]) / (sprint_id - 1), 1)
    ave_completed_text = '{0}%({1}/{2})'.format(ave_completed, base_value[3] + jira_commit[3], sprint_id - 1)
    x = PrettyTable()
    x.field_names = ['Sprint', "Committed", "Added", "Punted", "Completed", "Ave Completed", "Comments"]
    x.add_row([sprint_id, jira_commit[0], jira_commit[1], jira_commit[2], jira_commit[3], ave_completed_text, ''])
    print(x)


if __name__ == "__main__":
    capacity_dict = generate_team_capacity_to_dict(read_table_body_from_html_content(get_tic_individual_back_from_wiki()))
    tic_scrum_dashboard_html = get_tic_scrum_dashboard_back()
    last_sprint_values = generate_last_sprint_values(tic_scrum_dashboard_html)
    # generate_plan_metrics_table_value(capacity_dict, last_sprint_values)
    jira_velocity_metrics_html = get_jira_page_source_back(
        "https://jira.labs.quest.com/secure/RapidBoard.jspa?rapidView=1785&view=reporting&chart=velocityChart")
    jira_sp_values = get_sp_value_from_jira(jira_velocity_metrics_html)
    # generate_velocity_metrics_table_value(jira_sp_values, last_sprint_values)
    jira_velocity_metrics_html = get_jira_page_source_back(
        "https://jira.labs.quest.com/secure/RapidBoard.jspa?rapidView=1785&view=reporting&chart=sprintRetrospective&sprint={0}".format(sprint_number))
    jira_commited_values = get_issue_completion_metrics_from_jira(jira_velocity_metrics_html)
    generate_plan_metrics_table_value(capacity_dict, last_sprint_values)
    generate_velocity_metrics_table_value(jira_sp_values, last_sprint_values)
    generate_issue_completion_metrics_table_value(jira_commited_values, last_sprint_values)
    webcommon.get_driver().quit()
    tic_scrum_dashboard_url = "https://wiki.labs.quest.com/display/toadcloud/TIC+Scrum+Dashboard"
    print("\nYou can update TIC Scrum Dashboard Now: {0}".format(tic_scrum_dashboard_url))





















