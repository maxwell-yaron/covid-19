#!/usr/bin/env python3

from datetime import datetime, timedelta
from population import get_populations
import os
import requests
from urllib import request
from io import BytesIO, StringIO
import pandas as pd
import matplotlib.pyplot as plt
import json
import numpy as np
import re

TYPES = ['Confirmed','Recovered','Deaths']
OUTPUT = '/home/max/covid-19/resources'
BRANCH = 'master'
DAILY="https://raw.githubusercontent.com/CSSEGISandData/COVID-19/{branch}/csse_covid_19_data/csse_covid_19_daily_reports/{date}.csv"
SERIES = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/{branch}/csse_covid_19_data/csse_covid_19_time_series/time_series_19-covid-{type}.csv'
AGE_SHEET = '1jS24DjSPVWa4iuxuD4OAXrE3QeI8c9BC1hSlqr-NMiU'
AGE_GID = 1187587451

def download_google_sheet(sheet, gid, savepath, name):
  """
  Download sheet from Google Sheets as CSV.
  """
  URL='https://docs.google.com/spreadsheets/d/{id}/export?format=csv&id={id}&gid={gid}'.format(id=sheet, gid=gid)
  print("Downloading: " + URL)
  csv = requests.get(URL)
  outpath = os.path.join(savepath, name)
  with open(outpath, 'w') as f:
    f.write(csv.text)

ignore = ['Province/State','Country/Region','Lat','Long']

def download_daily(days = [1]):
  """
  Download daily reports.
  """
  for day in days:
    date = get_date(day)
    fpath = os.path.join(OUTPUT, date+'.csv')
    if not os.path.exists(fpath):
      url = DAILY.format(branch = BRANCH, date = date)
      print(url)
      request.urlretrieve(url, fpath)

def download_series_legacy(types = TYPES):
  """
  Download time series.
  """
  for type in types:
    fpath = os.path.join(OUTPUT, type+'.csv')
    url = SERIES.format(branch = BRANCH, type=type)
    print(url)
    request.urlretrieve(url, fpath)

def get_size(confirmed): 
  return int(np.log(confirmed[-1] + 1) * 5) 

def download_world():
  print('Downloading world...')
  URL_FMT = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/{}/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_{}_global.csv'
  BRANCH = 'master'
  cases = ['confirmed','deaths','recovered']
  data = {}
  for c in cases:
    url = URL_FMT.format(BRANCH, c)
    r = requests.get(url)
    df = pd.read_csv(StringIO(r.text))
    for idx, row in df.iterrows():
      if row['Province/State'] != 'nan':
        name = row['Country/Region']
      else:
        name = row['Province/State']
      d = {}
      d['name'] = name
      d['lat'] = row['Lat']
      d['lon'] = row['Long']
      days = row.drop(['Province/State','Country/Region','Lat','Long'])
      values = list(days.values)
      d[c] = values
      if c == 'confirmed':
        d['size'] = get_size(values)
      if name in data:
        data[name][c] = values
      else:
        data[name] = d
  fout = os.path.join('resources','World.json')
  with open(fout,'w') as f:
    json.dump(data, f)
  print(fout)

def download_counties():
  print('Downloading counties...')
  URL = 'https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-counties.csv'
  r = requests.get(URL)
  df = pd.read_csv(StringIO(r.text))
  # Get latest date.
  df['date'] = pd.to_datetime(df['date'])
  recent = df['date'].max()
  latest = df.loc[df['date'] == recent]
  data = {}
  for i, row in latest.iterrows():
    name = row['state']
    county = row['county']
    if name not in data:
      data[name] = {}
    data[name][county] = {'confirmed':row['cases'],'deaths':row['deaths']}
  return data

def download_states():
  print('Downloading states...')
  URL = 'https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-states.csv'
  r = requests.get(URL)
  df = pd.read_csv(StringIO(r.text))
  with open('resources/state_coords.json', 'r') as f:
    states = json.load(f)
  points = {}
  max_len = 0;
  for k, v in states.items():
    data = {'name': k, 'lat': v['lat'], 'lon': v['lon'], 'confirmed':[],'deaths':[],'recovered':[]}
    for i, row in df.iterrows():
      if row['state'] == k:
        data['confirmed'].append(row['cases'])
        data['deaths'].append(row['deaths'])
    data['size'] = get_size(data['confirmed'])
    points[k] = data
    max_len = max(max_len, len(data['confirmed']))

  # Backfill data
  for k, v in points.items():
    while len(v['confirmed']) < max_len:
      v['confirmed'].insert(0,0)
      v['deaths'].insert(0,0)

  # Fill counties.
  counties = download_counties()
  for k, v in counties.items():
    try:
      points[k]['counties'] = v
    except:
      pass
  outfile = 'resources/States.json'
  with open(outfile, 'w') as f:
    json.dump(points,f)
  print(outfile)

def download_populations():
  print('Downloading populations...')
  outfile = os.path.join(OUTPUT,'populations.json')
  d = get_populations()
  with open(outfile, 'w') as f:
    json.dump(d,f)
  print(outfile)

def main():
  os.makedirs(OUTPUT, exist_ok=True)
  download_world()
  download_populations()
  download_states()

if __name__ == '__main__':
  main()

