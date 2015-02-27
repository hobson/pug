import os

import pandas as pd

DATA_PATH = os.path.dirname(os.path.realpath(__file__))

fresno = pd.DataFrame.from_csv(os.path.join(DATA_PATH, 'weather_fresno.csv'))