#!/usr/bin/env python3
import argparse
import numpy as np
import sys
import os
import pandas as pd
from jinja2 import Template

TEMPLATE = "template.tpl"
TYPES = ['Confirmed','Recovered','Deaths']

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

def get_points(cases):
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
    points[name] = point
  for (name, lat, lon), row in cases['r'].iterrows():
    if name in points:
      vals = row.values
      (points[name]['recovered'], a) = sanitize_list(list(vals))
  for (name, lat, lon), row in cases['d'].iterrows():
    if name in points:
      vals = row.values
      (points[name]['deaths'], a) = sanitize_list(list(vals))

  return list(points.values())

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
  counties = counties[~counties['Province/State'].str.contains('D.C.', na=False)]
  # Copy county data for later.
  counties_copy = counties.copy()
  states = usa[~usa['Province/State'].str.contains(',|D.C.',na=False)]
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
  Get Country/Region data from loaded dataset. This also
  backports data to maintain US State time series.

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

def get_us_point(data):
  """
  Aggregate all us cases to get overall count for US.

  params:
  data(pd.DataFrame): input dataset

  returns(point): Data point for Javascript consumption.
  """
  sums = {}
  for k,df in data.items():
    df.groupby(['Country/Region'])
    df = df[df['Country/Region'] == 'US']
    df = df.drop(columns=['Province/State', 'Country/Region', 'Lat','Long'])
    sums[k] = df.sum()
  point = {}
  point['name'] = 'US'
  point['size'] = int(np.log(max(sums['Confirmed'].values)+1)) * 10
  point['lat'] = 38.9153534
  point['lon'] = -98.7777603
  point['confirmed'],a = sanitize_list(list(sums['Confirmed'].values))
  point['recovered'],a = sanitize_list(list(sums['Recovered'].values))
  point['deaths'],a = sanitize_list(list(sums['Deaths'].values))
  point['old'] = 0
  return point

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

def main(argv = sys.argv[1:]):
  parser = argparse.ArgumentParser()
  parser.add_argument('--savepath',type=str,default='docs',help="path to save html dashboard")
  args = parser.parse_args(argv)
  tpl = load_template()
  data = get_data()
  countries = get_points(get_countries(data))
  countries.append(get_us_point(data))
  states = get_points(get_provinces(data))
  html = tpl.render(points=countries+states, days = get_num_days(data['Confirmed']))
  output_file = os.path.join(args.savepath,'index.html')
  save_html(output_file, html)
  cases = get_total(data['Confirmed'])
  print('Saved: {}'.format(output_file))
  print('Total cases: {}'.format(cases))

if __name__ == '__main__':
  main()

