#!/usr/bin/env python3

import argparse
import json
import numpy as np
import sys
import os
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from jinja2 import Template

TEMPLATE = "template.tpl"
TYPES = ['Confirmed','Recovered','Deaths']

# Special case aggregates for unsupplied Countries/Regions
AGGREGATE = {
  'World':[0,-130.938346],
  'Australia':[-24.6483001,133.948055],
  'US':[38.9153534,-98.7777603],
  'China':[35.1378314,96.9347353],
}

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

# Need a mapping from code to name to make the data backwards compatible.
STATES = {
  "AL": "Alabama",
  "AK": "Alaska",
  "AZ": "Arizona",
  "AR": "Arkansas",
  "CA": "California",
  "CO": "Colorado",
  "CT": "Connecticut",
  "DE": "Delaware",
  "FL": "Florida",
  "GA": "Georgia",
  "HI": "Hawaii",
  "ID": "Idaho",
  "IL": "Illinois",
  "IN": "Indiana",
  "IA": "Iowa",
  "KS": "Kansas",
  "KY": "Kentucky",
  "LA": "Louisiana",
  "ME": "Maine",
  "MD": "Maryland",
  "MA": "Massachusetts",
  "MI": "Michigan",
  "MN": "Minnesota",
  "MS": "Mississippi",
  "MO": "Missouri",
  "MT": "Montana",
  "NE": "Nebraska",
  "NV": "Nevada",
  "NH": "New Hampshire",
  "NJ": "New Jersey",
  "NM": "New Mexico",
  "NY": "New York",
  "NC": "North Carolina",
  "ND": "North Dakota",
  "OH": "Ohio",
  "OK": "Oklahoma",
  "OR": "Oregon",
  "PA": "Pennsylvania",
  "RI": "Rhode Island",
  "SC": "South Carolina",
  "SD": "South Dakota",
  "TN": "Tennessee",
  "TX": "Texas",
  "UT": "Utah",
  "VT": "Vermont",
  "VA": "Virginia",
  "WA": "Washington",
  "WV": "West Virginia",
  "WI": "Wisconsin",
  "WY": "Wyoming",
}

def parse_dataset(type):
  """
  Parse csv file into a dataframe.

  params:
  type(str): oneof ['Confirmed','Recovered','Deaths']

  returns: pd.DataFrame
  """
  path = os.path.join('resources', type+'.csv')
  data = pd.read_csv(path)
  return data

def get_age_data():
  """
  Extract age based data.
  """
  csv = os.path.join('resources', 'Ages.csv')
  return pd.read_csv(csv, skiprows=1)

def get_data():
  """
  Get all data from each dataset

  returns(dict): {pd.DataFrame}
  """
  data = {}
  for t in TYPES:
    data[t] = parse_dataset(t)
  return data;

def sanitize_list(l):
  """
  Sanitize an input list to allow for detection of outdated data.

  params:
  l(list): list of data to be sanitized.

  returns(list, int): (sanitized list, number of days without update)
  """
  v = [i for i in l]
  try:
    while v[-1] == 0:
      v.pop()
    return (v, len(l) - len(v))
  except IndexError:
    if max(l) == 0:
      return l, 0
    raise ValueError("Invalid Data")

def get_provinces(data):
  """
  Get all province/state data.

  params:
  data(dict{pd.DataFrame}): data returned from get_data()

  returns(dict): {pd.DataFrame}
  """
  cases = {
    'c': get_province_data(data['Confirmed']),
    'r': get_province_data(data['Recovered']),
    'd': get_province_data(data['Deaths']),
  }
  return cases

def get_countries(data):
  """
  Get all country/region data.

  params:
  data(dict{pd.DataFrame}): data returned from get_data()

  returns(dict): {pd.DataFrame}
  """
  cases = {
    'c': get_country_data(data['Confirmed']),
    'r': get_country_data(data['Recovered']),
    'd': get_country_data(data['Deaths']),
  }
  return cases

def get_points(cases, ages=None, rates = False):
  """
  Convert case data into points for consumption by Javascript.

  params:
  cases(dict): Case data from either get_countries(), or get_provinces()

  returns(list): List of points.
  """
  points = {}
  for (name, lat, lon), row in cases['c'].iterrows():
    point = {}
    vals = row.values
    point['name'] = name
    point['size'] = int(np.log(max(vals)+1)) * 10
    point['lat'] = lat
    point['lon'] = lon
    (point['confirmed'], point['old']) = sanitize_list(list(vals))
    point['growth'] = growth_factor(point['confirmed'])
    points[name] = point
    # Populate age data if available.
    if ages is not None:
      a = ages[ages['country'] == name]
      point['ages'] = a['age'].dropna().values.tolist()
    else:
      point['ages'] = []
  for (name, lat, lon), row in cases['r'].iterrows():
    if name in points:
      vals = row.values
      (points[name]['recovered'], a) = sanitize_list(list(vals))
  for (name, lat, lon), row in cases['d'].iterrows():
    if name in points:
      vals = row.values
      (points[name]['deaths'], a) = sanitize_list(list(vals))
      if ages is not None:
        a = ages[ages['country'] == name]
        a=a[a['death'].fillna('0') != '0']
        died =  a['age'].dropna().values.tolist()
        points[name]['ages_died'] = died

  return list(points.values())

def first_non_zero(data):
  """
  Return the index before the first non zero element in a list.
  If the first value is non zero return 0, if all values are non zero return zero.

  params:
  data(list): List of values.

  return(int): Index before first non zero.
  """
  for i in range(len(data)):
    if data[i] > 0:
      return max([i-1,0])
  return 0;

def calculate_trends(points):
  """
  Fit data to both an exponential trend and a logistic trend and save data to corresponding point.

  params:
  points(list): list of points.

  return(None):
  """
  print("Calculating Trend Lines",end='', flush=True)
  for point in points:
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
      print('.',end='', flush=True)

    except:
      point['log_terms'] = []
      point['log_cov'] = []
      point['exp_terms'] = []
      point['exp_cov'] = []
  print('Done!')

def get_province_data(dataset):
  """
  Get State/Province data from loaded dataset. This also
  backports data to maintain US State time series.

  params:
  dataset(pd.Dataframe): Dataset to parse.
  """
  not_usa = dataset[dataset['Country/Region'] != 'US']
  usa = dataset[dataset['Country/Region'] == 'US']
  counties = usa[usa['Province/State'].str.contains(',',na=False)]
  counties = counties[~counties['Province/State'].str.contains('D.C.|U.S.', na=False)]
  # Copy county data for later.
  counties_copy = counties.copy()
  states = usa[~usa['Province/State'].str.contains(',|D.C.|U.S.',na=False)]
  # Modify region name so that they reflect the state
  for k,v in counties.iterrows():
    code = v['Province/State'].replace(' ','').split(',')[1]
    name = STATES[code]
    lat = states[states['Province/State'] == name]['Lat'].values[0]
    lon = states[states['Province/State'] == name]['Long'].values[0]
    counties.at[k,'Province/State'] = name
    counties.at[k,'Lat'] = lat
    counties.at[k,'Long'] = lon
  concat = pd.concat([not_usa, states, counties, counties_copy])
  return concat.groupby(['Province/State','Lat','Long']).sum()

def get_country_data(dataset):
  """
  Get Country/Region data from loaded dataset.

  params:
  dataset(pd.Dataframe): Dataset to parse.
  """
  return dataset.groupby(['Country/Region','Lat','Long']).sum()

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
  return len(data.columns.values) - 4

def get_aggregate_point(data, name, coord, ages = None):
  """
  Get a single point aggregated from other data.

  params:
  data(dict): dict of pd.DataFrames

  return(point): Aggregate point.
  """
  sums = {}
  for k,v in data.items():
    if name is not 'World':
      df = v[v['Country/Region'] == name]
    else:
      df = v
    df = df.drop(columns=['Country/Region', 'Province/State', 'Lat','Long'])
    sums[k] = df.sum()
  point = {}
  point['name'] = name
  point['size'] = int(np.log(max(sums['Confirmed'].values)+1)) * 10
  point['lat'] = coord[0]
  point['lon'] = coord[1]
  point['confirmed'],a = sanitize_list(list(sums['Confirmed'].values))
  point['recovered'],a = sanitize_list(list(sums['Recovered'].values))
  point['deaths'],a = sanitize_list(list(sums['Deaths'].values))
  point['growth'] = growth_factor(point['confirmed'])
  point['old'] = 0
  if ages is not None:
    if name is not 'World':
      if name == 'US':
        name = 'USA'
      df = ages[ages["country"] == name]
    else:
      df = ages
    # All cases.
    point['ages'] = df['age'].dropna().values.tolist();
    dead = df[df['death'].fillna('0') != '0']
    point['ages_died'] = dead['age'].dropna().values.tolist();
  else:
    point['ages'] = []
    point['ages_died'] = []
  return point

def point_list_to_dict(points):
  """
  Convert list of points to dict of points with name as key.
  params:
  points(list): list of points.

  return(dict): dict of points.
  """
  d = {}
  for point in points:
    d[point['name']] = point
  return d

def get_total(data, exclude = []):
  """
  Get the total for all entries with exclusions.

  params:
  data(pd.DataFrame): Dataset to parse.
  exclude(str): Countries to exclude.

  returns(int): Total count for parsed data.
  """
  total = 0
  data.groupby(['Country/Region'])
  for idx, row in data.iterrows():
    c = row['Country/Region']
    if c in exclude:
      continue
    if c == 'US':
      if ',' in row['Province/State']:
        continue
      else:
        pass
    total+=max((list(row.values)[4:]))
  return total

def fill_populations(l):
  path = os.path.join('resources', 'populations.json')
  with open(path, 'r') as f:
    j = json.loads(f.read())
  for i in l:
    name = i['name']
    try:
      pop = j[name]
    except:
      pop = 'N/A'
    i['population'] = pop

def main(argv = sys.argv[1:]):
  parser = argparse.ArgumentParser()
  parser.add_argument('--savepath',type=str,default='docs',help="path to save html dashboard")
  parser.add_argument('--trends',dest='trends', action='store_true', help="enable trend calculation")
  parser.add_argument('--notrends',dest='trends', action='store_false', help="enable trend calculation")
  parser.set_defaults(trends=True)
  args = parser.parse_args(argv)
  tpl = load_template()
  ages = get_age_data()
  data = get_data()
  countries = get_points(get_countries(data), ages, True)
  states = get_points(get_provinces(data))
  # Get aggregate points.
  extra = [get_aggregate_point(data,k,v,ages) for k,v in AGGREGATE.items()]

  #All points.
  all_points = countries + states + extra
  fill_populations(all_points)
  # Calculate trends.
  if args.trends:
    calculate_trends(all_points)
  points_dict = point_list_to_dict(all_points)
  html = tpl.render(points_dict=points_dict, days = get_num_days(data['Confirmed']))
  output_file = os.path.join(args.savepath,'index.html')
  save_html(output_file, html)
  cases = get_total(data['Confirmed'])
  print('Saved: {}'.format(output_file))
  print('Total cases: {}'.format(cases))

if __name__ == '__main__':
  np.seterr(divide='ignore', invalid='ignore')
  main()

