import sys
import pathlib

from rechtspraak import get_rechtspraak
from rechtspraak_metadata import get_rechtspraak_metadata

get_rechtspraak(max_ecli=50, sd='2022-08-01', save_file='y')
get_rechtspraak_metadata(save_file='y')

# print(df.head())
# print(df.shape)

