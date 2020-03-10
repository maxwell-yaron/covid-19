#!/usr/bin/env python3

import argparse
import sys
from datetime import datetime, timedelta
from scipy import stats
import os
from urllib import request
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import curve_fit
from matplotlib.backends.backend_pdf import PdfPages

VERBOSE=False
THRESH = 300
GRID = 2
PROJECT = ['US','China','France','Italy','South Korea', 'Iran', 'Australia', 'Switzerland']
TYPES = ['Confirmed','Recovered','Deaths']
OUTPUT = '/home/max/covid-19/resources'
ignore = ['Province/State','Country/Region','Lat','Long']

def logistic_growth(x, maximum, rate, center, offset):
  return maximum / (1 + np.exp(-rate*(x-center))) + offset;

def parse_dataset(type):
  path = os.path.join(OUTPUT, type+'.csv')
  data = pd.read_csv(path)
  return data

def get_date(past = 1):
  yesterday = datetime.today() - timedelta(days=past)
  date = yesterday.strftime('%m-%d-%Y')
  return date

def filter_data(dataset, column, filter):
  return dataset[dataset[column].str.contains(filter, na=False)]

def get_data_for_region(dataset, region):
  return filter_data(dataset, 'Province/State', region)

def get_data_for_country(dataset, region):
  return filter_data(dataset, 'Country/Region', region)

def join_region(region):
  return region.drop(columns=ignore).sum()

def drop_countries(dataset,drop):
  s = dataset
  for d in drop:
    s = s[~s['Country/Region'].str.contains(d, na=False)]
  return s

def plot_region(dataset, region):
  region = join_region(get_data_for_region(dataset, region)).values.transpose()
  data = [int(v) for v in region]
  plt.plot(range(len(data)),data)
  plt.show()

def fit_line(data):
  log_data = np.log(data)
  s, y, r, p, err = stats.linregress(range(len(log_data)), log_data)
  return {'slope':s, 'intercept':y, 'r_value':r, 'p_value':p, 'std_error':err}

def point_calc(fit, x):
  return fit['slope'] * x + fit['intercept']

def plot_data(ax, data, name):
  fit = fit_line(data)
  growth = 1 + fit['slope']
  r = fit['r_value']
  r2 = r * r
  x = range(len(data))
  ax.plot(x,data)
  m,c = np.polyfit(x, np.log(data), 1)
  y_fit = np.exp(m*x + c)
  ax.plot(x,y_fit,'k:')
  title = '{0}-({1:.2f}) - $R^2$({2:.2f})'.format(name, growth, r2)
  ax.set_title(title)
  ax.set_xlabel('Days')
  ax.set_ylabel('Cases')
  ax.set_yscale('log')

def plot_countries(dataset, countries, thresh, minimum = 10):
  cols = GRID
  rows = int(np.ceil(float(len(countries)) / cols))
  fig, ax = plt.subplots(nrows = rows, ncols = cols)
  names = countries
  idx = 0;
  fig.suptitle("Countries with greater than {} cases starting at the 50th case".format(thresh))
  for row in ax:
    for col in row:
      if idx > len(names) - 1:
        break;
      try:
        name = names[idx]
        region = join_region(get_data_for_country(dataset, name)).values.transpose()
        data = [int(v) for v in region]
        data = [v for v in data if v > minimum]
        plot_data(col, data, name)
        idx+=1
      except:
        continue

def plot_exp(x,rt,p0):
  y = [p0 * (1+rt)**t for t in x]
  plt.plot(x,y,'k')

def plot_single(region, name):
  y = join_region(region).values.transpose()
  x = range(len(y))
  plt.figure()
  plt.plot(x,y)
  plt.yscale('log')
  fit = fit_line(y)
  growth = 1 + fit['slope']
  r = fit['r_value']
  r2 = r * r
  m,c = np.polyfit(x, np.log(y), 1)
  y_fit = np.exp(m*x + c)
  plt.plot(x,y_fit,'k:')
  title = '{0}-({1:.2f}) - $R^2$({2:.2f})'.format(name, growth, r2)
  plt.title(title)
  plt.xlabel('Days')
  plt.ylabel('Cases')

def plot_projection(region, name):
  try:
    fig, ax = plt.subplots(nrows = 2, ncols = 1, constrained_layout=True)
    fig.suptitle('Logistic growth projection for {name}'.format(name=name))
    y = join_region(region).values.transpose()
    x = range(len(y))
    popt, pcov = curve_fit(logistic_growth, x, y, bounds = ([max(y),0,x[0],0],[1e9,10,x[-1],10]))
    x_end = int(popt[2] * 2)
    x_long = range(x_end)
    start_date = region.columns[4]
    start_datetime = datetime.strptime(start_date,'%m/%d/%y')
    inflection =  start_datetime + timedelta(days=round(popt[2]))
    date = inflection.strftime('%m-%d-%Y')

    plot = ax[0]
    table = ax[1]
    plot.plot(x,y)
    plot.plot(x_long, logistic_growth(x_long, *popt),'r:')
    plot.set_ylim((0,popt[0] * 1.1))
    plot.set_xlim((0,x_end))
    plot.set_xlabel('Days')
    plot.set_ylabel('Cases')
    plot.axvline(popt[2], linewidth=0.2, color='green')
    table.axis('off')
    table.table([[y[-1],popt[0],1+popt[1],date]], cellLoc='center', loc='center',colLabels=['Current Cases', 'Expected Cases', 'Growth rate', 'Inflection Date'])
  except Exception as e:
    print(e)
    pass

def state_totals(confirmed, recovered, deaths, states):
  data = []
  for state in states:
    c = get_number_of_cases(confirmed, state)
    r = get_number_of_cases(recovered, state)
    d = get_number_of_cases(deaths, state)
    d_rt = "%.2f%%"%(float(d) / c * 100);
    data.append([state, c, r, d, d_rt])
  fig = plt.figure()
  fig.suptitle("Daily coronavirus report for - {}".format(get_date()))
  ax = fig.add_subplot(1,1,1)

  ax.table(data, loc='center', cellLoc= 'center', colLabels = ["State", "Confirmed", "Recovered", "Deaths", "Death Rate"])
  ax.axis('off')

def get_data():
  data = {}
  for t in TYPES:
    data[t] = parse_dataset(t)
  return data;

def get_number_of_cases(dataset, region):
  region = get_data_for_region(dataset, region)
  if(VERBOSE):
    print(region)
  return region.iloc[:,-1].sum()

def get_countries(dataset, thresh = 100, top = 12):
  countries = dataset['Country/Region'].unique()
  count = {}
  for c in countries:
    if c == 'Others':
      continue
    data = dataset[dataset['Country/Region'] == c]
    last = data.iloc[:,-1]
    total = last.sum()
    if total > thresh:
      count[c] = total
  return count

def divide_chunks(l, n):
  for i in range(0, len(l), n):
    yield l[i:i+n]

def main(argv = sys.argv[1:]):
  data = get_data()
  confirmed = data['Confirmed']
  deaths = data['Deaths']
  recovered = data['Recovered']

  countries = get_countries(confirmed, THRESH)
  world = pd.concat([get_data_for_country(confirmed, c) for c in countries if "China" not in c])
  with PdfPages('multipage_pdf.pdf') as pdf:
    state_totals(confirmed, recovered, deaths, ['CA','CO','GA','WA'])
    pdf.savefig()
    plt.close()
    split_countries = list(divide_chunks(list(countries.keys()), GRID * GRID))
    for c in split_countries:
      plot_countries(confirmed, c, THRESH, 50)
      pdf.savefig()
      plt.close()
    plot_single(world, "World outside of China")
    pdf.savefig()
    plt.close()
    for p in PROJECT:
      plot_projection(get_data_for_country(confirmed, p),p)
      pdf.savefig()
      plt.close()
    plot_projection(drop_countries(confirmed, ['China']), 'World (excluding China)')
    pdf.savefig()
    plt.close()

if __name__ == '__main__':
  main()

