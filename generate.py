#!/usr/bin/env python3
from jinja2 import Template
import os
import numpy as np
import pandas as pd

TEMPLATE = "template.tpl"
FILENAME = "/tmp/index.html"
TYPES = ['Confirmed','Recovered','Deaths']


def parse_dataset(type):
  path = os.path.join('resources', type+'.csv')
  data = pd.read_csv(path)
  return data

def get_data():
  data = {}
  for t in TYPES:
    data[t] = parse_dataset(t)
  return data;

def sanitize_list(l):
  v = [i for i in l]
  try:
    while v[-1] == 0:
      v.pop()
    return v
  except IndexError:
    if max(l) == 0:
      return l
    raise ValueError("Invalid Data")

def get_provinces(data):
  cases = {
    'c': get_province_data(data['Confirmed']),
    'r': get_province_data(data['Recovered']),
    'd': get_province_data(data['Deaths']),
  }
  return cases

def get_countries(data):
  cases = {
    'c': get_country_data(data['Confirmed']),
    'r': get_country_data(data['Recovered']),
    'd': get_country_data(data['Deaths']),
  }
  return cases

def get_points(cases):
  points = {}
  for (name, lat, lon), row in cases['c'].iterrows():
    point = {}
    vals = row.values
    point['name'] = name
    point['size'] = int(np.log(max(vals)+1)) * 10
    point['lat'] = lat
    point['lon'] = lon
    point['confirmed'] = sanitize_list(list(vals))
    points[name] = point
  for (name, lat, lon), row in cases['r'].iterrows():
    if name in points:
      vals = row.values
      points[name]['recovered'] = sanitize_list(list(vals))
  for (name, lat, lon), row in cases['d'].iterrows():
    if name in points:
      vals = row.values
      points[name]['deaths'] = sanitize_list(list(vals))

  return list(points.values())

def get_province_data(dataset):
  return dataset.groupby(['Province/State','Lat','Long']).sum()

def get_country_data(dataset):
  return dataset.groupby(['Country/Region','Lat','Long']).sum()

def load_template():
  with open(TEMPLATE, "r") as f:
    tpl = Template(f.read())
  return tpl

def save_html(filename, html):
  print(filename)
  with open(filename, "w") as f:
    f.write(html)

def get_total(data, exclude = []):
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

def main():
  tpl = load_template()
  data = get_data()
  countries = get_points(get_countries(data))
  states = get_points(get_provinces(data))
  html = tpl.render(points=countries+states)
  save_html(FILENAME, html)
  print(get_total(data['Confirmed'], 'China'))

if __name__ == '__main__':
  main()

