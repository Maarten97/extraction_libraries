import numpy as np
import pandas as pd
import re
import dateparser
from echr_extractor.clean_ref import clean_pattern



def open_metadata(PATH_metadata):
    """
    Finds the ECHR metadata file and loads it into a dataframe
    
    param filename_metadata: string with path to metadata
    """
    try:
        df = pd.read_csv(PATH_metadata)  # change hard coded path
        return df
    except FileNotFoundError:
        print("File not found. Please check the path to the metadata file.")
        return False

def concat_metadata(df):
    agg_func = {'itemid' : 'first', 'appno' : 'first', 'article' : 'first', 'conclusion' : 'first' , 'docname' : 'first' , 'doctype' : 'first',
                'doctypebranch' : 'first', 'ecli' : 'first', 'importance' : 'first', 'judgementdate' : 'first', 'languageisocode' : ', '.join, 'originatingbody' : 'first',
                'violation' : 'first', 'nonviolation' : 'first', 'extractedappno' : 'first', 'scl' : 'first'}
    new_df = df.groupby('ecli').agg(agg_func)
    print(new_df)
    return new_df

def get_language_from_metadata(df):
    df = concat_metadata(df)
    df.to_json('langisocode-nodes.json', orient="records")

def metadata_to_nodesedgeslist(df):
    """
    Returns a dataframe where column 'article' only contains a certain article

    param df: the complete dataframe from the metadata
    """
    
    return df


def retrieve_nodes_list(df):
    """
    Returns a dataframe where 'ecli' is moved to the first column.

    param df: the dataframe after article filter
    """
    df = metadata_to_nodesedgeslist(df)
    col = df.pop("ecli")
    df.insert(1, col.name, col)
    df.drop(df.columns[0], axis=1, inplace=True)
    return df


def retrieve_edges_list(df, df_unfiltered):
    """
    Returns a dataframe consisting of 2 columns 'ecli' and 'reference' which
    indicate a reference link between cases.

    params:
    df -- the node list extracted from the metadata
    df_unfiltered -- the complete dataframe from the metadata
    """
    edges = pd.DataFrame(columns=['ecli', 'references'])

    count = 0
    tot_num_refs = 0
    missing_cases = []
    for index, item in df.iterrows():
        eclis = []
        app_number = []
        extracted_appnos = []
        if item.extractedappno is not np.nan:
            extracted_appnos = item.extractedappno.split(';') 

        if item.scl is not np.nan:
            """
            Split the references from the scl column i nto a list of references.

            Example:
            references in string: "Ali v. Switzerland, 5 August 1998, § 32, Reports of Judgments and 
            Decisions 1998-V;Sevgi Erdogan v. Turkey (striking out), no. 28492/95, 29 April 2003"

            ["Ali v. Switzerland, 5 August 1998, § 32, Reports of Judgments and 
            Decisions 1998-V", "Sevgi Erdogan v. Turkey (striking out), no. 
            28492/95, 29 April 2003"]
            """
            ref_list = item.scl.split(';')
            new_ref_list = []
            for ref in ref_list:
                ref = re.sub('\n', '', ref)
                new_ref_list.append(ref)

            tot_num_refs = tot_num_refs + len(ref_list)

            for ref in new_ref_list:
                app_number = re.findall("[0-9]{3,5}\/[0-9]{2}", ref) ################
                if len(extracted_appnos) > 0:
                    app_number = app_number + extracted_appnos
                # app_number = app_number + extracted_appnos
                app_number = set(app_number)
                
                if len(app_number) > 0:
                    # get dataframe with all possible cases by application number
                    if len(app_number) > 1:
                        app_number = [';'.join(app_number)]
                    case = lookup_app_number(app_number, df_unfiltered)
                else: # if no application number in reference
                    # get dataframe with all possible cases by casename
                    case = lookup_casename(ref, df_unfiltered)

                if len(case) == 0:
                    case = lookup_casename(ref, df_unfiltered)

                components = ref.split(',')
                # get the year of case
                year_from_ref = get_year_from_ref(components)

                # remove cases in different language than reference
                for id, it in case.iterrows():
                    if 'v.' in components[0]:
                        lang = 'ENG'
                    else:
                        lang = 'FRE'

                    if lang not in it.languageisocode:
                        case = case[case['languageisocode'].str.contains(lang, regex=False, flags=re.IGNORECASE)]

                for id, i in case.iterrows():
                    if i.judgementdate is np.nan:
                        continue
                    date = dateparser.parse(i.judgementdate)
                    year_from_case = date.year

                    if year_from_case - year_from_ref == 0:
                        case = case[case['judgementdate'].str.contains(str(year_from_ref), regex=False, flags=re.IGNORECASE)]

                #case = metadata_to_nodesedgeslist(case)

                if len(case) > 0:
                    if len(case) > 3:
                        print("stop")
                    for _,row in case.iterrows():
                        eclis.append(row.ecli)
                else:
                    count = count + 1
                    missing_cases.append(ref)

            eclis = set(eclis)

            #add ecli to edges list
            if len(eclis) == 0:
                continue
            else:
                edges = pd.concat(
                    [edges, pd.DataFrame.from_records([{'ecli': item.ecli, 'references': list(eclis)}])])

    print("num missed cases: ", count)
    print("total num of refs: ", tot_num_refs)
    missing_cases_set = set(missing_cases)
    missing_cases = list(missing_cases_set)
    
    # Store missing references
    missing_df = pd.DataFrame(missing_cases)
    # missing_df.to_csv('C:/Users/Chloe/PycharmProjects/case-law-explorer/data/echr/missing_cases.csv', index=False, encoding='utf-8')
    edges = edges.groupby('ecli', as_index=False).agg({'references' : 'sum'})
    return edges

def lookup_app_number(pattern, df):
    """
    Returns a list with rows containing the cases linked to the found app numbers.
    """
    row = df.loc[df['appno'].isin(pattern)]

    if row.empty:
        return pd.DataFrame()
    elif row.shape[0] > 1:
        return row
    else:
        return row


def lookup_casename(ref, df):
    """
    Process the reference for lookup in metadata.
    Returns the rows corresponding to the cases.

    - Example of the processing (2 variants) -

    Original reference from scl:
    - Hentrich v. France, 22 September 1994, § 42, Series A no. 296-A
    - Eur. Court H.R. James and Others judgment of 21 February 1986,
    Series A no. 98, p. 46, para. 81

    Split on ',' and take first item:
    Hentrich v. France
    Eur. Court H.R. James and Others judgment of 21 February 1986

    If certain pattern from CLEAN_REF in case name, then remove:
    Eur. Court H.R. James and Others judgment of 21 February 1986 -->
        James and Others

    Change name to upper case and add additional text to match metadata:
    Hentrich v. France --> CASE OF HENTRICH V. FRANCE
    James and Others --> CASE OF JAMES AND OTHERS
    """
    name = get_casename(ref)
    
    # DEV note: In case, add more patterns to clean_ref.py in future
    patterns = clean_pattern

    uptext = name.upper()

    if 'NO.' in uptext:
        uptext = uptext.replace('NO.', 'No.')

    if 'BV' in uptext:
        uptext = uptext.replace('BV', 'B.V.')

    if 'v.' in name:
        uptext = uptext.replace('V.', 'v.')
        lang = 'ENG'
    else:
        uptext = uptext.replace('C.', 'c.')
        lang = 'FRE'

    for pattern in patterns:
        uptext = re.sub(pattern, '', uptext)

    uptext = re.sub(r'\[.*', "", uptext)
    uptext = uptext.strip()
    row = df[df['docname'].str.contains(uptext, regex=False, flags=re.IGNORECASE)]

    # if len(row) == 0:
    #     print("no cases matched: ", name)

    return row

def get_casename(ref):
    count = 0
    if 'v.' in ref:
        slice_at_versus = ref.split('v.')  # skip if typo (count how many)
    elif 'c.' in ref:
        slice_at_versus = ref.split('c.')
    else:
        count = count + 1
        name = ref.split(',')
        return name[0]

    num_commas = slice_at_versus[0].count(',')

    if num_commas > 0:
        num_commas = num_commas + 1
        name = ",".join(ref.split(",", num_commas)[:num_commas])
    else:
        name = ref.split(',')
        return name[0]
    return name

def get_year_from_ref(ref):
    for component in ref:
        if '§' in component:
            continue
        component = re.sub('judgment of ', "", component)
        if dateparser.parse(component) is not None:
            date = dateparser.parse(component)
        elif ("ECHR" in component or "CEDH" in component):
            if ("ECHR" in component or "CEDH" in component):
                date = re.sub('ECHR ', '', component)
                date = re.sub('CEDH ', '', date)
                date = date.strip()
                date = re.sub('-.*', '', date)
                date = re.sub('\s.*', '', date)
                date = dateparser.parse(date)
   
    try:
        return date.year
    except:
        return 0



def echr_nodes_edges(metadata_path):
    """
    Create nodes and edges list for the ECHR data.
    """
    print('\n--- COLLECTING METADATA ---\n')
    data = open_metadata(metadata_path)

    print('\n--- EXTRACTING NODES LIST ---\n')
    nodes = retrieve_nodes_list(data)
    # get_language_from_metadata(nodes)

    print('\n--- EXTRACTING EDGES LIST ---\n')
    edges = retrieve_edges_list(nodes, data)

    # nodes.to_json(JSON_ECHR_NODES, orient="records")
    # edges.to_json(JSON_ECHR_EDGES, orient="records")
    return nodes, edges