import requests
import re
from bs4 import BeautifulSoup
from io import BytesIO, StringIO
from zipfile import ZipFile
import pandas as pd

def get_state_population():
  URL = "https://www2.census.gov/programs-surveys/popest/datasets/2010-2019/state/detail/SCPRC-EST2019-18+POP-RES.csv"
  d = requests.get(URL)
  df = pd.read_csv(StringIO(d.text))
  data = {}
  for i, r in df.iterrows():
    num = int(r['POPESTIMATE2019'])
    data[r['NAME']] = f'{num:,}'
  return data

def get_world_population():
  URL = "https://en.wikipedia.org/wiki/List_of_countries_by_population_(United_Nations)"
  r = requests.get(URL)
  html = BeautifulSoup(r.text, features='html.parser')
  table_div = html.findAll('table',{'class':'wikitable'})[1]
  rows = table_div.findAll('tr')
  data = {}
  for r in rows:
    cell = r.findAll('td')
    try:
      name = cell[0].get_text().strip()
      name = re.sub(r'\[[a-z]\]','', name)
      pop = cell[3].get_text().strip()
      data[name] = pop
    except:
      pass
  return data

def get_populations():
  d = {**get_world_population(), **get_state_population()}
  d['US'] = d.pop('United States')
  return d

get_populations()
