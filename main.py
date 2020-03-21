#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import json
from pathlib import Path
from datetime import date, datetime
from urllib import request, parse

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt


sns.set(style="ticks")#darkgrid, whitegrid,dark,white,ticks
#sns.set(font_scale = 0.5)
sns.set_context("paper", rc={"font.size":8,"axes.titlesize":20,"axes.labelsize":15})#paper,talk,notebook
fig, ax = plt.subplots()

covid_data_path = os.path.join(os.environ['GITHUB_WORKSPACE'], 'covid-data', 'csse_covid_19_data', 'csse_covid_19_time_series')

cases_path = os.path.join(covid_data_path, 'time_series_19-covid-Confirmed.csv')
recoveries_path = os.path.join(covid_data_path, 'time_series_19-covid-Recovered.csv')
deaths_path = os.path.join(covid_data_path, 'time_series_19-covid-Deaths.csv')

cases = pd.read_csv(cases_path)
recoveries = pd.read_csv(recoveries_path)
deaths = pd.read_csv(deaths_path)

in_cases = cases[cases['Country/Region'] == 'India']
in_recoveries = recoveries[recoveries['Country/Region'] == 'India']
in_deaths = deaths[deaths['Country/Region'] == 'India']

in_cases_df = in_cases[in_cases.columns[4:]]
in_recoveries_df = in_recoveries[in_recoveries.columns[4:]]
in_deaths_df = in_deaths[in_deaths.columns[4:]]

sns.barplot(data=in_cases_df, palette=sns.color_palette("Oranges", len(in_cases_df.columns)), ax=ax)
sns.barplot(data=in_recoveries_df, palette=sns.color_palette("Greens", len(in_recoveries_df.columns)), ax=ax)
sns.barplot(data=in_deaths_df, palette=sns.color_palette("Reds", len(in_deaths_df.columns)), ax=ax)

plt.title('COVID-19 Cases, Deaths and Recovery Graph')
ax.set(xlabel='Time ->', ylabel='Cases')
plt.xticks(fontsize=6, rotation=75)
plt.yticks(fontsize=6)
ax.axhline(int(in_cases_df.iloc[:, -1]), ls='--')
plt.gca().set_position([0, 0, 1, 1])
plt.savefig("graph.svg", format='svg', dpi=1200, bbox_inches='tight')
plt.show()#must be in the end otherwise saving to svg won't work

namespace = {'current_time': datetime.now(), 'commit_sha': os.environ['GITHUB_SHA']}

with open('template.html') as f:
  template_html = f.read()

formatted_html = template_html.format(**namespace)

with open('index.html', 'w+') as f:
  f.write(formatted_html)

Path(os.path.join(os.environ['GITHUB_WORKSPACE'], 'covid19-in', 'datasets', 'timeseries_records')).mkdir(parents=True, exist_ok=True)
Path(os.path.join(os.environ['GITHUB_WORKSPACE'], 'covid19-in', 'datasets', 'statewise_distribution')).mkdir(parents=True, exist_ok=True)

url = 'http://www.mohfw.gov.in/'
header = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36'}
#param_dict = {"f": "json", "singleLine": "delhi, IND", "maxLocations": 1}
#params = parse.urlencode(param_dict).encode('UTF-8')
req = request.Request(url, headers=header)#, data=params)
response = request.urlopen(req)

table_list = pd.read_html(response, header=0)
table_df = table_list[0].head(-1)

def geocode(city):
    url = 'https://geocode.arcgis.com/arcgis/rest/services/World/GeocodeServer/findAddressCandidates'
    header = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36'}

    param_dict = {"f": "json", "singleLine": f"{city}, IND", "maxLocations": 1}
    params = parse.urlencode(param_dict).encode('UTF-8')
    req = request.Request(url, headers=header, data=params)

    try:
      response = request.urlopen(req)
    except Exception as e:
      #logging.error("Request Failed", exc_info=True)
      print("Request Failed")
      raise e
    else:
      #logging.debug(response.getcode())
      #logging.debug(response.info())
      pass

    if response.getcode() == 200:
      response_dict = json.load(response)
      return (response_dict['candidates'][0]["location"]["x"], response_dict['candidates'][0]["location"]["y"])

def add_lat_lon(df):
    df['Lon'], df['Lat'] = zip(*df['Name of State / UT'].map(geocode))
    return df

table_df = add_lat_lon(table_df)
table_df.to_csv(f'./datasets/statewise_distribution/{str(date.today())}.csv', sep=',', encoding='utf-8', index=False)

#####################
in_cases_df.index = pd.Index(['cases'], name='time')
in_deaths_df.index = pd.Index(['deaths'], name='time')
in_recoveries_df.index = pd.Index(['recoveries'], name='time')

cases_T = in_cases_df.T
deaths_T = in_deaths_df.T
recoveries_T = in_recoveries_df.T
temp_df = cases_T.join([deaths_T, recoveries_T])

final_df = pd.melt(temp_df.reset_index(), id_vars='index', var_name='category', value_name='value')
final_df.to_csv(f'./datasets/timeseries_records/categories_timeseries.csv', sep=',', encoding='utf-8', index=False)


#p = {"cases": sns.color_palette("Oranges", 51), "deaths" : sns.color_palette("Reds", 51), "rec": #sns.color_palette("Greens", 51)}
#sns.catplot(x='index', y='value', hue='category', data=e, kind='bar', palette=p)
#plt.show()


