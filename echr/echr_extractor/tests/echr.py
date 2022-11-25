from ECHR_metadata_harvester import read_echr_metadata
from pathlib import Path
from os.path import basename, dirname, abspath, join, exists, relpath, isfile
from os import makedirs, getenv, listdir
import time
import sys
import logging
import pandas as pd
from datetime import date, datetime

# Windows path fix, if system is windows then it replaces the forward slashes for the regex statement later
WINDOWS_SYSTEM = False
if sys.platform =="win32":
    WINDOWS_SYSTEM = True
def windows_path(original):
    return original.replace('\\', '/')

# local data folder structure
DIR_ROOT = dirname(dirname(abspath(__file__)))
DIR_DATA = join(DIR_ROOT, 'data')
DIR_DATA_RAW = join(DIR_DATA, 'raw')
DIR_DATA_RECHTSPRAAK = join(DIR_DATA, 'Rechtspraak')
DIR_DATA_PROCESSED = join(DIR_DATA, 'processed')


# data file names
# DIR_RECHTSPRAAK = join(DIR_DATA, 'Rechtspraak', 'OpenDataUitspraken')
DIR_ECHR = join(DIR_DATA, 'echr')
# CELLAR_DIR = join(DIR_DATA, 'cellar')
# CELLAR_ARCHIVE_DIR=join(CELLAR_DIR,'archive')
# CSV_OPENDATA_INDEX = DIR_RECHTSPRAAK + '_index.csv'         # eclis and decision dates of OpenDataUitspraken files
# CSV_RS_CASES = 'RS_cases.csv'                               # metadata of RS cases
# CSV_RS_OPINIONS = 'RS_opinions.csv'                         # metadata of RS opinions
# CSV_CELLAR_CASES = 'cellar_csv_data.csv'                    # Metadata of CELLAR cases
# CSV_CELLAR_UPDATE = 'cellar_csv_update.csv'                 # Update file for the main cellar file
# CSV_RS_INDEX = 'RS_index.csv'                               # eclis, decision dates and relations of RS cases and opinions
# CSV_LI_CASES = 'LI_cases.csv'                               # metadata of LI cases
# CSV_CASE_CITATIONS = 'caselaw_citations.csv'                # citations of RS cases and opinions
# CSV_LEGISLATION_CITATIONS = 'legislation_citations.csv'     # cited legislation of RS cases and opinions
# CSV_LIDO_ECLIS_FAILED = 'LIDO_eclis_failed.csv'
# CSV_DDB_ECLIS_FAILED = 'DDB_eclis_failed.csv'
# CSV_OS_ECLIS_FAILED = 'OS_eclis_failed.csv'
CSV_ECHR_CASES = join(DIR_ECHR, 'ECHR_metadata.csv')
CSV_ECHR_CASES_NODES = join(DIR_ECHR,'ECHR_nodes.csv')
CSV_ECHR_CASES_EDGES = join(DIR_ECHR,"ECHR_edges.csv")
JSON_FULL_TEXT_CELLAR=join(DIR_DATA_PROCESSED,'cellar_full_text.json')


# raw data:
def get_path_raw(file_name):
    return join(DIR_DATA_RAW, file_name)


# processed data
def get_path_processed(file_name):
    return join(DIR_DATA_PROCESSED, file_name.split('.csv')[0] + '_clean.csv')

class Storage:
    def __init__(self, location):
        if location not in ('local'):
            print('Storage location must be either "local" or "aws". Setting to "local".')
            location = 'local'
        self.location = location
        # self.s3_bucket_name = getenv('S3_BUCKET_NAME')
        # self.s3_bucket = None
        # self.s3_client = None
        self.pipeline_input_path = None
        self.pipeline_output_paths = None
        self.pipeline_last_updated = date(1900, 1, 1)

        print(f'\nSetting up {self.location} storage ...')
        self._setup()

    def _setup(self):
        # create local data folder structure, if it doesn't exist yet
        # for d in [dirname(DIR_RECHTSPRAAK), DIR_DATA_RAW, DIR_DATA_PROCESSED, CELLAR_DIR,CELLAR_ARCHIVE_DIR,DIR_ECHR]:
        for d in [DIR_ECHR]:

            makedirs(d, exist_ok=True)

        # if self.location == 'aws':
        #     # create an S3 bucket in the region of the configured AWS IAM user account
        #     try:
        #         region = getenv('AWS_REGION')
        #         s3_client = boto3.client('s3', region_name=region)
        #         aws_location = {'LocationConstraint': region}
        #         s3_client.create_bucket(Bucket=self.s3_bucket_name, CreateBucketConfiguration=aws_location)
        #     except ClientError as e:
        #         if e.response['Error']['Code'] == 'BucketAlreadyOwnedByYou' or \
        #                 e.response['Error']['Code'] == 'BucketAlreadyExists':
        #             logging.warning(f'S3 bucket "{self.s3_bucket_name}" already exists. Content might be overwritten.')
        #         else:
        #             raise e
        #     self.s3_bucket = boto3.resource('s3').Bucket(self.s3_bucket_name)
        #     self.s3_client = boto3.client('s3')
        # print('Storage set up.')

    def setup_pipeline(self, output_paths=None, input_path=None):
        self.pipeline_input_path = input_path
        self.pipeline_output_paths = output_paths

        # fetch output data
        # if self.pipeline_output_paths:
        #     print(f'\nFetching output data from {self.location} storage ...')
        #     for path in self.pipeline_output_paths:
        #         if exists(path) :
        #             if get_path_processed(CSV_CELLAR_CASES) in path: # Modification added for cellar updating
        #                 logging.error(f'{path} exists locally! It will be updated with the newest download.')
        #             else:
        #                 logging.error(f'{path} exists locally! Move/rename local file before starting pipeline.')
        #                 sys.exit(2)
        #         if path.endswith('.csv'):
        #             self.fetch_data([path])

            # retrieve output date of last update
            # self.pipeline_last_updated = self.fetch_last_updated(self.pipeline_output_paths)

        # fetch input data
        if self.pipeline_input_path:
            print(f'\nFetching input data from {self.location} storage ...')
            self.fetch_data([self.pipeline_input_path])
            # retrieve input date of last update
            last_updated_input = self.fetch_last_updated([self.pipeline_input_path])

            # if output date of last update after input date of last update: need to update input first
            if last_updated_input < self.pipeline_last_updated:
                logging.error(f'Input data {basename(self.pipeline_input_path)} is older than output data. '
                              f'Please update input data first.')
                sys.exit(2)

    def finish_pipeline(self):
        if self.pipeline_output_paths:
            self.upload_data(self.pipeline_output_paths)

    def fetch_data(self, paths):
        def not_found(file_path):
            msg = file_path + ' does not exist! Consider switching storage location' \
                         ' or re-running earlier steps of the pipeline.'
            if file_path == self.pipeline_input_path:
                logging.error(msg)
                sys.exit(2)
            else:
                logging.warning(msg)

        def fetch_data_local(file_path):
            # exit if input does not exist
            if not exists(file_path):
                not_found(file_path)
            else:
                print('Local data ready.')

        # def fetch_data_aws(file_path):
        #     if exists(file_path):
        #         logging.error(f'{file_path} exists locally! Move/rename local file before fetching data from aws.')
        #         #sys.exit(2)

        #     elif file_path == DIR_RECHTSPRAAK:
        #         # paginate through all items listed in folder
        #         paginator = self.s3_client.get_paginator('list_objects_v2')
        #         folder_name = relpath(file_path, DIR_ROOT) + '/'
        #         pages = paginator.paginate(Bucket=self.s3_bucket_name, Prefix=folder_name)
        #         empty = True
        #         for page in pages:
        #             empty = False
        #             if 'Contents' in page:
        #                 for obj in page['Contents']:
        #                     yearmonth = dirname(relpath(obj['Key'], folder_name)).split('/')[1]
        #                     if date(int(yearmonth[:4]), int(yearmonth[4:]), 1) > self.pipeline_last_updated:
        #                         key = obj['Key']
        #                         makedirs(dirname(join(DIR_ROOT, key)), exist_ok=True)
        #                         self.s3_bucket.download_file(key, join(DIR_ROOT, key))
        #         if empty:
        #             not_found(file_path)

        #     else:
        #         try:
        #             makedirs(dirname(file_path), exist_ok=True)
        #             self.s3_bucket.download_file(relpath(file_path, DIR_ROOT), file_path)
        #         except ClientError as e:
        #             if e.response['Error']['Code'] == '404':
        #                 not_found(file_path)

        #     print(f'{basename(file_path)} fetched.')

        if self.location == 'local':
            for path in paths:
                fetch_data_local(path)
        # elif self.location == 'aws':
        #     for path in paths:
        #         fetch_data_aws(path)

    def upload_data(self, paths):
        # def upload_to_aws(file_path):
        #     if isfile(file_path):
        #         try:
        #             self.s3_bucket.upload_file(file_path, relpath(file_path, DIR_ROOT))
        #         except ClientError as e:
        #             logging.error(e)
        #     else:
        #         for sub_path in listdir(file_path):
        #             upload_to_aws(join(file_path, sub_path))

        # if self.location == 'aws':
        #     for path in paths:
        #         upload_to_aws(path)
        #         print(basename(path), 'loaded to aws.')
        # else:
        print('Local data updated.')

    def fetch_last_updated(self, paths):
        def date_map(file_path):
            default = ('date_decision', lambda x: date.fromisoformat(x))
            d_map = {
                get_path_raw(CSV_LI_CASES): ('EnactmentDate', lambda x: datetime.strptime(x, "%Y%m%d").date())
            }
            return d_map.get(file_path, default)

        def default_date(file_path):
            print(f'Setting start date of {basename(file_path)} to 1900-01-01.')
            return date(1900, 1, 1)

        def last_updated(file_path):
            # if file_path == DIR_RECHTSPRAAK:
            #     self.fetch_data([CSV_OPENDATA_INDEX])
            #     file_path = CSV_OPENDATA_INDEX
            # if WINDOWS_SYSTEM:
            #     if re.match(rf'^{windows_path(CELLAR_DIR)}/.*\.json$',windows_path(file_path)):
            #         if self.location == 'local':
            #             # Go through existing JSON files and use their filename to determine when the last
            #             # update was.
            #             # Alternatively, this could be switched to loading all the JSONs and checking the
            #             # max last modification date.
            #             new_date = datetime(1900, 1, 1)
            #             for filename in listdir(CELLAR_DIR):
            #                 match = re.match(
            #                     r'^(\d{4})-(\d{2})-(\d{2})T(\d{2})_(\d{2})\_(\d{2})\.json$', filename)
            #                 if not match:
            #                     continue

            #                 new_date = max(
            #                     new_date,
            #                     datetime(
            #                         int(match[1]), int(match[2]), int(match[3]),
            #                         int(match[4]), int(match[5]), int(match[6])
            #                     )
            #                 )
            #         return new_date
            # else:
            #     if re.match(rf'^{CELLAR_DIR}/.*\.json$', file_path):
            #         if self.location == 'local':
            #             # Go through existing JSON files and use their filename to determine when the last
            #             # update was.
            #             # Alternatively, this could be switched to loading all the JSONs and checking the
            #             # max last modification date.
            #             new_date = datetime(1900, 1, 1)
            #             for filename in listdir(CELLAR_DIR):
            #                 match = re.match(
            #                     r'^(\d{4})-(\d{2})-(\d{2})T(\d{2})_(\d{2})\_(\d{2})\.json$', filename)
            #                 if not match:
            #                     continue

            #                 new_date = max(
            #                     new_date,
            #                     datetime(
            #                         int(match[1]), int(match[2]), int(match[3]),
            #                         int(match[4]), int(match[5]), int(match[6])
            #                     )
            #                 )
            #             return new_date
            if DIR_DATA_RAW  in file_path or DIR_DATA_PROCESSED in file_path:
                return default_date(file_path)

            if file_path.endswith('.csv'):
                import pandas as pd
                try:
                    date_name, date_function = date_map(file_path)
                    df = pd.read_csv(file_path, usecols=[date_name], dtype=str)
                    return max(df[date_name].apply(date_function))
                except FileNotFoundError:
                    logging.warning(file_path + ' not found.')
                    return default_date(file_path)

            logging.warning(basename(file_path) + ' is not a .csv file.')
            return default_date(file_path)

        last_updated_dates = []
        for path in paths:
            this_last_updated = last_updated(path)
            print(f'- Last updated {basename(path)}:\t {this_last_updated}')
            last_updated_dates.append(this_last_updated)

        return min(last_updated_dates)

def get_echr(sd='2022-08-01', ed=None,count=None, save_file='y'):
    # set up script arguments
    # parser = argparse.ArgumentParser()
    # parser.add_argument('storage', choices=['local', 'aws'], help='location to save output data to')
    # parser.add_argument('--count', help='number of documents to retrieve', type=int, required=False)
    # args = parser.parse_args(argv)

    # set up locations
    print('\n--- PREPARATION ---\n')
    print('OUTPUT DATA STORAGE:\t')
    print('OUTPUT:\t\t\t', CSV_ECHR_CASES)

    storage = Storage(location='local')
    storage.setup_pipeline(output_paths=[CSV_ECHR_CASES])

    last_updated = storage.pipeline_last_updated
    print('\nSTART DATE (LAST UPDATE):\t', last_updated.isoformat())

    print('\n--- START ---')
    start = time.time()

    print("--- Extract ECHR data")
    # arg_end_id = args.count if args.count else None
    df, resultcount = read_echr_metadata(end_id= count, fields=['itemid', 'documentcollectionid2', 'languageisocode'],
                                         verbose=True)

    print(f'ECHR data shape: {df.shape}')
    print(f'Columns extracted: {list(df.columns)}')

    print("--- Filter ECHR data")
    df_eng = df.loc[df['languageisocode'] == 'ENG']

    print(f'df before language filtering: {df.shape}')
    print(f'df after language filtering: {df_eng.shape}')

    print("--- Load ECHR data")
    if save_file == "y":
        df.to_csv(CSV_ECHR_CASES)
        print("--- Saved ECHR data")
        return df

    print(f"\nUpdating local storage ...")
    storage.finish_pipeline()

    end = time.time()
    print("\n--- DONE ---")
    print("Time taken: ", time.strftime('%H:%M:%S', time.gmtime(end - start)))
    return df

