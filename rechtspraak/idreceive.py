from datetime import datetime, timedelta
import os

import rechtspraak_extractor as rex
#
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


def circle_date(start_date, end_date):

    # Assuming your input startdate is in the format '2024-05-15'

    date_format = '%Y-%m-%d'

    # Convert the input startdate string to a datetime object
    start_date = datetime.strptime(start_date, date_format)
    end_date = datetime.strptime(end_date, date_format)

    # Loop from startdate to yesterday (inclusive)
    while start_date <= end_date:
        output_date = start_date.strftime(date_format)
        # to_date = (start_date + timedelta(days=7)).strftime(date_format)
        to_date = output_date
        print(f'Output date: {output_date} and to date: {to_date}')

        # try:
        request_id_per_date(output_date, to_date)
        start_date = start_date + timedelta(days=1)
        # except Exception as e:
        #     # Handle the exception (e.g., print an error message)
        #     write_error(f"Error occurred for value {output_date}. Exception type: {type(e).__name__}")
        #     start_date += timedelta(days=7)
        #     continue


def write_error(text):
    current_datetime = datetime.now()
    formatted_date_time = current_datetime.strftime("%Y%m%d_%H%M")
    output_file = formatted_date_time + ".txt"

    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "error", output_file)

    if not os.path.isfile(output_path):
        with open(output_path, "w") as txtfile:
            txtfile.write(text + "\n")
    else:
        with open(output_path, "a") as txtfile:
            txtfile.write(text + "\n")

#
# def check_language(list_rs):
#     return list_rs


def request_id_per_date(startdate, enddate):
    rex.get_rechtspraak(max_ecli=1000, sd=startdate, ed=enddate, save_file='y')


if __name__ == '__main__':
    # df = rex.get_rechtspraak(max_ecli=1000, sd='2022-08-01', ed='2022-08-01', save_file='n')
    # print(df)
    input_startdate = '2023-01-14'
    input_enddate = '2023-01-16'
    circle_date(input_startdate, input_enddate)
