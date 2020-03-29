#!/usr/bin/python3

import json
import os
import argparse
import sys
import subprocess as sp

def load_data():
  path = os.path.join('resources','World.json')
  with open(path, 'r') as f:
    data = json.load(f)
  return data

def run_sir(data):
  c = [str(i) for i in data['confirmed']]
  d = [str(i) for i in data['deaths']]
  r = [str(i) for i in data['recovered']]
  if not (len(c) == len(d) == len(r)):
    raise ValueError("Array lengths are not the same")
  flags = [
    '--alsologtostderr',
    '--v=1',
    ]
  cmd_fmt = '{bin} --confirmed {c} --deaths {d} --recovered {r} {flags}'
  cmd = cmd_fmt.format(
      bin='./sir_model',
      c=','.join(c),
      d=','.join(d),
      r=','.join(r),
      flags = ' '.join(flags))
  out = sp.check_output(cmd.split())
  print(out)

def main(argv=sys.argv[1:]):
  parser = argparse.ArgumentParser()
  parser.add_argument('--region',required=True)
  args = parser.parse_args(argv)
  data = load_data()
  r = data[args.region]
  run_sir(r)

if __name__ == '__main__':
  main()
