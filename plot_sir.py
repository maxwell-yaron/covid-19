#!/usr/bin/env python3

import matplotlib.pyplot as plt
import numpy as np

def plot_sir(s, ki, kr, i0 = 1, r0 = 0):
  t = 70
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
  print(inf[68])
  plt.figure(0)
  plt.plot(sus)
  plt.plot(inf)
  plt.plot(rem)
  plt.show()

plot_sir(1e9,6.1e-11,0.0296685)
