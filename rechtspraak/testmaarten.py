import time
from pathlib import Path

import requests

import rechtspraak_extractor as rex
import pandas as pd

# Define base url
RECHTSPRAAK_METADATA_API_BASE_URL = "http://data.rechtspraak.nl/uitspraken/content?id=" # old one = "https://uitspraken.rechtspraak.nl/#!/details?id="
return_type = "&return=DOC"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36',
    'Referer': '',  # Set an empty referer
}

# -----------------------------------------------------------------------------------------------------------------------
#
# # For rechtspraak
#
# # To get the rechtspraak data in a dataframe:
# df = rex.get_rechtspraak(max_ecli=100, sd='2022-08-01', save_file='n')  # Gets 100 ECLIs from 1st August 2022
#
# # To save rechtspraak data as a CSV file:
# rex.get_rechtspraak(max_ecli=100, sd='2022-08-01', save_file='y')
#
# -----------------------------------------------------------------------------------------------------------------------
#
# # For rechtspraak metadata
#
# # To get metadata as a dataframe from rechtspraak data (as a dataframe):
# df_metadata = rex.get_rechtspraak_metadata(save_file='n', dataframe=df)
#
# # To get metadata as a dataframe from rechtspraak file (as a dataframe):
# df_metadata = rex.get_rechtspraak_metadata(save_file='n', filename='rechtspraak.csv')
#
# # To get metadata as a dataframe from rechtspraak data (saved as CSV file):
# rex.get_rechtspraak_metadata(save_file='y', dataframe=df)
#
# # To get metadata and save as a CSV file:
# rex.get_rechtspraak_metadata(save_file='y', filename='rechtspraak.csv')
#
# -----------------------------------------------------------------------------------------------------------------------
#
# # filename='rechtspraak.csv' - filename.csv is a file from the data folder created by get_rechtspraak method
# # dataframe=df - df is a dataframe created by get_rechtspraak method
#
# # Will not get any metadata
# df = rex.get_rechtspraak_metadata(save_file='n')
#
# # Will get the metadata of all the files in the data folder
# rex.get_rechtspraak_metadata(save_file='y')

def get_data_from_api(ecli):
    #See row 323

    url = RECHTSPRAAK_METADATA_API_BASE_URL + ecli + return_type
    httpcode = check_api(url)
    print(f'HTTP CODE FOR {httpcode} WITH ECLI {ecli}')
    if httpcode == 403:
        print(f'Forbidden HTTP for ECLI {ecli} with url {url}')



def check_api(url):
    response = requests.get(f"{url}", headers=headers)
    # Return with the response code
    return response.status_code


def getowndata(dataframe):
    if dataframe is not None:
        output = pd.DataFrame(columns=['ecli', 'full_text', 'creator', 'date_decision', 'issued',
                                       'zaaknummer','type','relations','references', 'subject', 'procedure',
                                        'inhoudsindicatie','hasVersion'])
        ecli_list = list(dataframe.loc[:, 'id'])
        # Path('temp_rs_data').mkdir(parents=True, exist_ok=True)
        time.sleep(1)

        for ecli in ecli_list:
            time.sleep(1)
            get_data_from_api(ecli)


if __name__ == '__main__':
    rex.get_rechtspraak(max_ecli=20, sd='2024-08-01', save_file='y')
    # print(df)
    # print("df executed, now optaining metadata")
    # rex.get_rechtspraak_metadata(save_file='y', dataframe=df)
    # print("Metadata command executed, main finished")

    rs_data = pd.read_csv('data/' + 'rechtspraak_2024-08-01_2024-05-30_08-48-55.csv')
    getowndata(rs_data)

    # rex.get_rechtspraak_metadata(save_file='y', filename='rechtspraak_2024-08-01_2024-05-30_08-48-55.csv')
    # get_data_from_api('ECLI:NL:RVS:2024:2145')