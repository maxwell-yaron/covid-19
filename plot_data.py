#!/usr/bin/env python3

import json
import argparse
import sys
from datetime import datetime, timedelta
from scipy import stats
import os
from urllib import request
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as colors
from mpl_toolkits.basemap import Basemap
import numpy as np
from scipy.optimize import curve_fit
from matplotlib.backends.backend_pdf import PdfPages

INCUBATION=14
VERBOSE=False
THRESH = 300
GRID = 2
PROJECT = ['US','China','France','Italy','Korea', 'Iran', 'Australia', 'Switzerland', 'Japan']
TYPES = ['Confirmed','Recovered','Deaths']
OUTPUT = '/home/max/covid-19/resources'
ignore = ['Province/State','Country/Region','Lat','Long']

def draw_map(name, coords, dataset):
  llon=coords['ll_long']
  llat=coords['ll_lat']
  rlon=coords['ur_long']
  rlat=coords['ur_lat']
  clat = (llat+rlat) / 2
  clon = (llon+rlon) / 2
  m = Basemap(llcrnrlon=llon,llcrnrlat=llat,urcrnrlon=rlon,urcrnrlat=rlat, epsg=2163)

  m.arcgisimage(service='NatGeo_World_Map', xpixels = 2000, verbose= True)

  data = get_data_for_region(dataset, name)
  case_lats = data['Lat'].values.transpose()
  case_longs = data['Long'].values.transpose()
  x,y = m(case_longs,case_lats)
  m.scatter(x,y,c='r')

  for city, coord in coords['cities'].items():
    x,y = m(*coord)
    m.plot(x,y,'b,')
    plt.text(x,y,city)

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
  data = filter_data(dataset, 'Country/Region', region)
  if region == 'US':
    # Drop counties
    return data[data['Province/State'].str.contains(',', na=False)]
  return data

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
  ax.set_title(title, fontsize=8)
  ax.set_xlabel('Days', fontsize=8)
  ax.set_ylabel('Cases', fontsize=8)
  ax.set_yscale('log')

def plot_growth_rate(dataset, name):
  fig = plt.figure()
  fig.suptitle(r'Growth factor $[\frac{\Delta{N}_{d}}{\Delta{N}_{d-1}}]$ for - %s'%(name))
  ax = fig.add_subplot()
  data = np.array(join_region(dataset).values.transpose())
  diffs = data[1:] - data[:-1]
  growth = diffs[1:]/diffs[:-1]
  growth[np.isinf(growth)] = 0
  growth[np.isnan(growth)] = 0
  inc = growth[-INCUBATION:]
  inc_x = range(len(growth)-INCUBATION,len(growth),1)
  m,c = np.polyfit(inc_x, inc, 1)
  y_fit = m  * inc_x + c
  ax.set_title(r'Trend $\frac{{dy}}{{dt}}=%.3f$ based on %d day incubation period'%(m, INCUBATION), fontsize=8)
  ax.plot(inc_x, y_fit, 'r:', linewidth=0.5)
  ax.plot(range(len(growth)), growth,'.:')
  ax.axhline(1.0, linewidth=0.2, color='green')

def plot_countries(dataset, countries, thresh, minimum = 10):
  cols = GRID
  rows = int(np.ceil(float(len(countries)) / cols))
  fig, ax = plt.subplots(nrows = rows, ncols = cols, tight_layout=True)
  names = countries
  idx = 0;
  #fig.suptitle("Countries with greater than {} cases starting at the 50th case".format(thresh), fontsize = 10)
  for row in ax:
    try:
      l = len(row)
    except:
      return False
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
        return False
  return True

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
    fig.suptitle(r'Logistic growth projection $[\frac{L}{1+{e}^{-{k}({x}-{x}_{0})}}+{b}]$ for %s'%(name))
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
    plot.plot(x_long, logistic_growth(x_long, *popt),'r:', linewidth=0.5)
    hue = np.interp(np.abs(x[-1] - popt[2]),(0,np.abs(popt[2] - popt[2] * 1.2)),(0,110)) / 360
    color = colors.hsv_to_rgb((hue,10./100,1))
    plot.set_facecolor(color)
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
  parser = argparse.ArgumentParser()
  parser.add_argument('--verbose',default=False,type=bool)
  parser.add_argument('--incubation',default=14,type=int)
  parser.add_argument('--thresh',default=300,type=int)
  parser.add_argument('--output',default=None,type=str)
  parser.add_argument('--savepath',default='/tmp',type=str)
  args = parser.parse_args(argv)
  THRESH = args.thresh
  VERBOSE = args.verbose
  INCUBATION = args.incubation
  data = get_data()
  confirmed = data['Confirmed']
  deaths = data['Deaths']
  recovered = data['Recovered']

  countries = get_countries(confirmed, THRESH)
  world = pd.concat([get_data_for_country(confirmed, c) for c in countries if "China" not in c])
  outfile = os.path.join(args.savepath, '{}.pdf'.format(get_date()))
  if args.output:
    outfile = os.path.join(args.savepath, '{}.pdf'.format(args.output))
  with PdfPages(outfile) as pdf:
    state_totals(confirmed, recovered, deaths, ['CA','CO','GA','WA'])
    pdf.savefig()
    plt.close()
    countries_list = list(countries.keys())
    split_countries = list(divide_chunks(countries_list, GRID * GRID))
    for c in split_countries:
      if plot_countries(confirmed, c, THRESH, 50):
        pdf.savefig()
        plt.close()
    plot_single(world, "World outside of China")
    pdf.savefig()
    plt.close()
    for p in PROJECT:
      country = get_data_for_country(confirmed, p)
      plot_growth_rate(country, p)
      pdf.savefig()
      plt.close()
      plot_projection(country,p)
      pdf.savefig()
      plt.close()
    plot_projection(drop_countries(confirmed, ['China']), 'World (excluding China)')
    pdf.savefig()
    plt.close()

if __name__ == '__main__':
  np.seterr(divide='ignore', invalid='ignore')
  main()

