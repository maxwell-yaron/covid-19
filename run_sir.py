#!/usr/bin/python3

import json
import os
import argparse
import sys
import subprocess as sp
import matplotlib.pyplot as plt
import numpy as np

def fill_populations(l):
  path = os.path.join('resources', 'populations.json')
  with open(path, 'r') as f:
    j = json.loads(f.read())
  for k,v in l.items():
    try:
      p = int(j[k].replace(',',''))
      v['population'] = p
    except:
      v['population'] = 'N/A'

def load_data():
  path = os.path.join('resources','World.json')
  with open(path, 'r') as f:
    data = json.load(f)
  return data

def run_sir(data, trim, pop):
  c = [str(i) for i in data['confirmed']]
  d = [str(i) for i in data['deaths']]
  r = [str(i) for i in data['recovered']]
  if not (len(c) == len(d) == len(r)):
    raise ValueError("Array lengths are not the same")
  flags = [
    '--alsologtostderr',
    '--v=2',
    ]
  cmd_fmt = '{bin} --confirmed {c} --deaths {d} --recovered {r} --population {p} --trim {t} {flags}'
  cmd = cmd_fmt.format(
      bin='./sir_model',
      c=','.join(c),
      d=','.join(d),
      r=','.join(r),
      p=pop,
      t=trim,
      flags = ' '.join(flags))
  out = sp.check_output(cmd.split())
  return out

def plot_sir(s, ki, kr, i0 = 1, r0 = 0, days = 0):
  i0 = max(i0,1)
  t = days
  i = i0
  r = r0
  sp = 0
  si = 0
  sr = 0
  sus = []
  inf = []
  rem = []
  for _ in range(t):
    sus.append(s)
    inf.append(i)
    rem.append(r)
    sp = -ki * i * s
    ip = ki * i * s - kr * i
    rp = kr * i
    s += sp
    i += ip
    r += rp
  print('peak: {}'.format(np.argmax(inf)))
  plt.plot(inf)
  plt.plot(rem)

def plot_curr(pop, data):
  c = np.array(data['confirmed'])
  d = np.array(data['deaths'])
  r = np.array(data['recovered'])
  rem = d + r;
  sus = [pop - i for i in rem]
  inf = c - rem;
  print(inf[-1])
  plt.figure(1)
  plt.plot(rem)
  plt.plot(inf)

def main(argv=sys.argv[1:]):
  parser = argparse.ArgumentParser()
  parser.add_argument('--region',required=True)
  parser.add_argument('--trim',type=int, default=0)
  parser.add_argument('--percent',type=float, default=1.0)
  parser.add_argument('--population',type=float)
  args = parser.parse_args(argv)
  data = load_data()
  fill_populations(data)
  r = data[args.region]
  conf = r['confirmed'][-1]
  days = len(r['confirmed'])
  pop = int(r['population']*args.percent)
  sir = run_sir(r, args.trim, pop)
  out = json.loads(sir)
  print(out)
  plt.figure(0)
  plot_sir(out['population'],out['ki'],out['kr'],out['i0'],out['r0'], days)
  plot_curr(100000, r)
  plt.show()

if __name__ == '__main__':
  main()
