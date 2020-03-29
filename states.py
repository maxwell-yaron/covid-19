import json
from bs4 import BeautifulSoup
import requests
import os

def clean_coords(s):
  c = s.split('/')[2]
  v = c.split(';')
  lat = float(v[0])
  lon = float(v[1].split('(')[0].strip().replace('\ufeff',''))
  return lat,lon

def download_coords():
  URL = 'https://en.wikipedia.org/wiki/List_of_geographic_centers_of_the_United_States'
  r = requests.get(URL)
  html = BeautifulSoup(r.text, features='html.parser')
  tbl = html.findAll('table', {'class':'wikitable'})[1]
  rows = tbl.findAll('tr')
  data = {}
  for row in rows[1:]:
    cell = row.findAll('td')
    name = cell[0].get_text().strip()
    lat,lon = clean_coords(cell[2].get_text())
    data[name] = {'lat':lat,'lon':lon}
  return data

def save_coords():
  path = os.path.join('resources','state_coords.json')
  data = download_coords()
  with open(path, 'w') as f:
    json.dump(data,f)

save_coords()
