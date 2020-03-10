#!/usr/bin/env python3

from datetime import datetime, timedelta
import os
from urllib import request
import pandas as pd
import matplotlib.pyplot as plt
import re

TYPES = ['Confirmed','Recovered','Deaths']
OUTPUT = '/home/max/covid-19/resources'
BRANCH = 'master'
DAILY="https://raw.githubusercontent.com/CSSEGISandData/COVID-19/{branch}/csse_covid_19_data/csse_covid_19_daily_reports/{date}.csv"
SERIES = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/{branch}/csse_covid_19_data/csse_covid_19_time_series/time_series_19-covid-{type}.csv'

ignore = ['Province/State','Country/Region','Lat','Long']

def download_daily(days = [1]):
  for day in days:
    date = get_date(day)
    fpath = os.path.join(OUTPUT, date+'.csv')
    if not os.path.exists(fpath):
      url = DAILY.format(branch = BRANCH, date = date)
      print(url)
      request.urlretrieve(url, fpath)

def download_series(types = TYPES):
  for type in types:
    fpath = os.path.join(OUTPUT, type+'.csv')
    url = SERIES.format(branch = BRANCH, type=type)
    print(url)
    request.urlretrieve(url, fpath)

def main():
  os.makedirs(OUTPUT, exist_ok=True)
  download_series()

if __name__ == '__main__':
  main()

