#!/usr/bin/env python3

import argparse
import json
import numpy as np
import sys
import os
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from datetime import datetime
from jinja2 import Template

TEMPLATE = "template.tpl"

def logistic_growth(x, maximum, rate, center, offset):
  return maximum / (1 + np.exp(-rate*(x-center))) + offset;

def exponential_growth(x,initial_pop,r, a):
  return initial_pop * ((1 + r)**(x-a))

def growth_factor(dataset):
  """
  Get the current growth factor for a dataset.
  dN/dN-1

  params:
  dataset(list): list of cases by day.

  return(list): growth factor over time.
  """
  data = np.array(dataset)
  d = data[1:] - data[:-1]
  growth = d[1:]/d[:-1]
  growth[np.isinf(growth)] = 0
  growth[np.isnan(growth)] = 0
  return growth.tolist()

def calculate_trends(points):
  """
  Fit data to both an exponential trend and a logistic trend and save data to corresponding point.

  params:
  points(list): list of points.

  return(None):
  """
  print("Calculating Trend Lines",end='', flush=True)
  for k, point in points.items():
    # Calculate growth rates if enabled.
    y = point['confirmed']
    x = range(len(y))
    try:
      log_opt, log_cov = curve_fit(logistic_growth, x, y , bounds = ([max(y),0,x[0],0],[1e9,10,x[-1] * 1.2,10]))
      exp_opt, exp_cov = curve_fit(exponential_growth, x, y, bounds = ([1,0,1],[200,1,100]))

      point['log_terms'] = log_opt.tolist()
      point['log_cov'] = log_cov.tolist()
      point['exp_terms'] = exp_opt.tolist()
      point['exp_cov'] = exp_cov.tolist()
      point['growth'] = growth_factor(y)
      print('.',end='', flush=True)

    except:
      point['growth'] = 'N/A'
      point['log_terms'] = []
      point['log_cov'] = []
      point['exp_terms'] = []
      point['exp_cov'] = []
  print('Done!')

def load_template():
  """
  Load Jinja2 HTML template from file.

  returns(str): Template string
  """
  with open(TEMPLATE, "r") as f:
    tpl = Template(f.read())
  return tpl

def save_html(filename, html):
  """
  Save HTML to file
  """
  with open(filename, "w") as f:
    f.write(html)

def get_num_days(data):
  """
  Get the number of days that have been recorded.

  returns(int): number of days.
  """
  return len(data['US']['confirmed'])

def get_total(data):
  """
  Get the total for all entries with exclusions.

  params:
  data(pd.DataFrame): Dataset to parse.
  exclude(str): Countries to exclude.

  returns(int): Total count for parsed data.
  """
  total = 0;
  for k,v in data.items():
    total+=v['confirmed'][-1]
  return total

def fill_populations(l):
  path = os.path.join('resources', 'populations.json')
  with open(path, 'r') as f:
    j = json.loads(f.read())
  for k,v in l.items():
    try:
      v['population'] = j[k]
    except:
      v['population'] = 'N/A'

def get_world_points():
  path = os.path.join('resources','World.json')
  with open(path, 'r') as f:
    data = json.load(f)
  return data

def get_state_points():
  path = os.path.join('resources','States.json')
  with open(path, 'r') as f:
    data = json.load(f)
  return data

def main(argv = sys.argv[1:]):
  parser = argparse.ArgumentParser()
  parser.add_argument('--savepath',type=str,default='docs',help="path to save html dashboard")
  parser.add_argument('--trends',dest='trends', action='store_true', help="enable trend calculation")
  parser.add_argument('--notrends',dest='trends', action='store_false', help="enable trend calculation")
  parser.set_defaults(trends=True)
  args = parser.parse_args(argv)
  tpl = load_template()
  world = get_world_points()
  states = get_state_points()
  points_dict = {**world, **states}
  fill_populations(points_dict)
  # Calculate trends.
  if args.trends:
    calculate_trends(points_dict)
  html = tpl.render(points_dict=points_dict, days = get_num_days(points_dict))
  output_file = os.path.join(args.savepath,'index.html')
  save_html(output_file, html)
  cases = get_total(world)
  print('Saved: {}'.format(output_file))
  print('Total cases: {}'.format(cases))

if __name__ == '__main__':
  np.seterr(divide='ignore', invalid='ignore')
  main()
