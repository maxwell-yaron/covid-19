#!/usr/bin/env python3

from datetime import datetime, timedelta
from population import get_populations
import os
import requests
from urllib import request
import pandas as pd
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup
import json
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

def download_series(types = TYPES):
  """
  Download time series.
  """
  for type in types:
    fpath = os.path.join(OUTPUT, type+'.csv')
    url = SERIES.format(branch = BRANCH, type=type)
    print(url)
    request.urlretrieve(url, fpath)

def download_counties(outpath):
  URL = 'https://topic.newsbreak.com/covid-19.html'
  r = requests.get(URL)
  html = BeautifulSoup(r.text,features='html.parser')
  data = html.body.find('script', attrs={'id':'__NEXT_DATA__'}).text
  j = json.loads(data)
  states = j['props']['pageProps']['data']['us_stats']
  output = {}
  for s in states:
    name = s['tl']
    counties = s['counties']
    county_stats = []
    for c in counties:
      county_stats.append({'name':c['nm'], 'c':c['f'],'d':c['d']})
    if len(county_stats):
      output[name] = county_stats
  outfile = os.path.join(outpath,'us_counties.json')
  print(outfile)
  with open(outfile, 'w') as f:
    json.dump(output, f)

def download_populations():
  outfile = os.path.join(OUTPUT,'populations.json')
  d = get_populations()
  with open(outfile, 'w') as f:
    json.dump(d,f)
  print(outfile)

def main():
  os.makedirs(OUTPUT, exist_ok=True)
  download_series()
  download_counties(OUTPUT)
  download_google_sheet(AGE_SHEET, AGE_GID, OUTPUT, 'Ages.csv')
  download_populations()

if __name__ == '__main__':
  main()

