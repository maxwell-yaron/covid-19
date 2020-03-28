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
  return int(np.log(confirmed[-1] + 1) * 10) 

def download_series():
  URL_FMT = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/{}/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_{}_global.csv'
  BRANCH = 'master'
  cases = ['confirmed','deaths','recovered']
  data = {}
  for c in cases:
    url = URL_FMT.format(BRANCH, c)
    print(url)
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

def download_populations():
  outfile = os.path.join(OUTPUT,'populations.json')
  d = get_populations()
  with open(outfile, 'w') as f:
    json.dump(d,f)
  print(outfile)

def main():
  os.makedirs(OUTPUT, exist_ok=True)
  download_series()
  download_populations()

if __name__ == '__main__':
  main()

