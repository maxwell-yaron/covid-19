import requests
import pandas as pd
from io import StringIO
sheet = '1jS24DjSPVWa4iuxuD4OAXrE3QeI8c9BC1hSlqr-NMiU'
gid=1187587451
URL='https://docs.google.com/spreadsheets/d/{id}/export?format=csv&id={id}&gid={gid}'.format(id=sheet, gid=gid)
csv = requests.get(URL)
fp = StringIO(csv.text)
data = pd.read_csv(fp, skiprows=1)
print(data['age'])
