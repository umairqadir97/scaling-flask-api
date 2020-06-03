import pickle
import operator
import pandas as pd
import os
import traceback
from cleanco import cleanco
import re
import json
import requests
from collections import defaultdict


# Global Variables Used All Over
quantity_keywords = ["qty", "quantity", "数量", "eau", "shortage", "excess", "demand"]
item_number_keywords = ["item", "no."]
invalid_brand_names = {'lt', 'ltd', 'app', 'manufacturer'}   # will be removed before brand_name check
invalid_part_numbers = {'packing', 'ltd'}   # will be removed before brand_name check
possible_splitter = ["#", "(", "-", " ", "/"]   # Only these splitter are allowed for brand/ part_No


def read_lines_with_lower_strip(file_path):
    with open(file_path, 'r') as fp:
        return [str(line).lower().strip() for line in fp.read().split("\n") if line]


# Load Keywords for searching headers
brand_name_header_keywords = read_lines_with_lower_strip("./data/column_headers/brand_name_header.txt")
part_number_header_keywords = read_lines_with_lower_strip("./data/column_headers/part_number_header.txt")
quantity_header_keywords = read_lines_with_lower_strip("./data/column_headers/quantity_header.txt")


def read_lines(file_path):
    with open(file_path, 'r') as fp:
        return [line for line in fp.read().split("\n") if line]


def read_dictionary_json(file_path):
    with open(file_path, "r") as fp:
        return json.load(fp)


def string_quantity_to_integer(string_number):
    try:
        if string_number != string_number:
            # nan converted to zero
            return 0
        if type(string_number) in [int, float]:
            return int(float(string_number))
        string_number = re.sub(r"[^0-9k\.\-]*", "", str(string_number).strip().lower())   # preserver minus sign
        is_k = True if string_number.strip().endswith("k") else False
        if is_k:
            element = re.sub(r"[^0-9\.]*", "", string_number.replace("k", "")).strip()
            if bool(re.match(r'^(\d+\.\d+)?$', element)):
                return int(float(element) * 1000.0)
            else:
                return int(element) * 1000
        return int(float(re.sub(r"[^0-9\.\-]*", "", string_number).strip()))
    except Exception as e:
        return False


def write_to_pickle(obj, file_path):
    with open(file_path, 'wb') as fp:
        pickle.dump(obj, fp)


def read_from_pickle(file_path):
    with open(file_path, 'rb') as fp:
        return pickle.load(fp)


def remove_punctuations(text):
    # alphanumeric plus spaces allowed
    return re.sub(r"[^a-zA-Z0-9 ]*", "", str(text)).strip().lower()


def clean_brand_name(text):
    # remove punctuations
    return remove_punctuations(cleanco(str(text)).clean_name())


def clean_part_number(pn):
    # only alphanumeric allowed
    return re.sub(r"[^a-zA-Z0-9]*", "", str(pn)).strip().lower()


def is_integer(element):
    try:
        if type(element) == int:
            return True
        if element != element:
            return False

        qty_related_words = ["pieces", "piece", "k", "qty"]   # not implemented yet, .replace() used instead
        element = str(element).lower().replace(r'k', '').replace("pieces", "").replace("piece", "").replace(",", "").strip()
        if element.isdigit():
            return True
        elif float(element) or int(element):
            return True
        return False
    except Exception as e:
        return False


def get_tables_from_url(url):
    tables = pd.read_html(url, encoding="utf-8")
    return tables


def exist_brand_alias_or_part(row, BRAND_NAMES, BRAND_ALIASES, PART_NUMBERS):
    return any([set(map(clean_brand_name, row)).intersection(BRAND_NAMES),
                set(map(clean_brand_name, row)).intersection(BRAND_ALIASES),
                set(map(clean_part_number, row)).intersection(PART_NUMBERS)])


def fix_data_frame(df, BRAND_NAMES, BRAND_ALIASES, PART_NUMBERS):
    global quantity_keywords
    global invalid_brand_names
    df.columns = pd.Series([str(c) for c in df.columns])
    df = df.dropna(axis=0, how="all").drop_duplicates()
    df = df.dropna(axis=1, how="all")
    table_header = {"status": False, "row_number": None}
    # removing 'manufacturer' and 'L/T' from matches, since it's mostly part of header
    # following condition will check if no brand_name, brand_alias and part_number exists first row
    # plus none of the column headers is integer, then surely it's a table header
    df_columns = [str(elt).lower() for elt in df.columns]
    if any([qty_elt in str(df_elt).lower() for df_elt in df_columns for qty_elt in quantity_keywords]):
        if not exist_brand_alias_or_part(df_columns, BRAND_NAMES, BRAND_ALIASES, PART_NUMBERS) and not \
                any([is_integer(clm) for clm in df_columns]):
            return df, {"status": True, "row_number": -1}

    for row in df.iterrows():
        if any([qty_elt in str(df_elt).lower() for df_elt in row[1] for qty_elt in quantity_keywords]):
            if not exist_brand_alias_or_part(row[1], BRAND_NAMES, BRAND_ALIASES, PART_NUMBERS) and not \
                    any([is_integer(clm) for clm in row[1]]):
                table_header = {"status": True, "row_number": row[0]}
                break

    # if exist_brand_alias_or_part(df_columns, BRAND_NAMES, BRAND_ALIASES, PART_NUMBERS) or \
    #         any([is_integer(clm) for clm in df_columns]):
    #     table_header = {"status": False, "row_number": None}
    #     break
    return df, table_header


def get_brand_name_column(df, table_header, BRAND_NAMES, BRAND_ALIASES):
    try:
        if table_header["status"] and table_header["row_number"] != -1:
            df = df[table_header["row_number"]+1:]
        brands = BRAND_NAMES.union(BRAND_ALIASES)
        columns_ratio = {}
        for column in df.columns:
            unique_elements = set([x for x in list(map(clean_brand_name, [elt for elt in df[column].values if elt and elt == elt])) if x])
            if not unique_elements:
                continue
            intersection = brands.intersection(unique_elements)
            columns_ratio[column] = len(intersection) / (df.shape[0] / len(unique_elements))
        if not columns_ratio or sum(columns_ratio.values()) == 0:
            return False
        return max(columns_ratio.items(), key=operator.itemgetter(1))[0]
    except Exception:
        traceback.print_exc()
        return False


def get_quantity_column(df, table_header):
    try:
        def is_qty_clm(clm_name, header_row, table_header):
            global quantity_keywords
            if table_header["status"] and table_header["row_number"] != -1:
                if any([elt in str(header_row[clm_name]).lower() for elt in quantity_keywords]):
                    return True
            if any([elt in str(clm_name).lower() for elt in quantity_keywords]):
                return True
            return False

        quantity_column, suggested_quantity_column = False, False
        header_row = None   # make a copy of DF without header_row for ratios
        if table_header["status"]:
            if table_header["row_number"] != -1:
                header_row = df.iloc[table_header["row_number"]]
                df = df[table_header["row_number"]+1:]
            else:
                header_row = pd.Series(df.columns)
        # print("printing DF:\n\n", df.shape, df.columns)

        columns_ratio = {}
        for column in df.columns:
            unique_elements = set([str(elt).lower().strip() for elt in df[column] if elt and elt == elt])
            if not unique_elements:
                continue

            integer_elements = set([elt for elt in unique_elements if is_integer(elt)])
            if integer_elements and max([string_quantity_to_integer(elt) for elt in integer_elements]) > 1000000:
                if not is_qty_clm(column, header_row, table_header):
                    continue   # integer values more than 100k/row then ignore that row [or column]
            columns_ratio[column] = len(integer_elements) / len(set(unique_elements))

        if table_header["status"]:
            non_qty_clms = []
            for k in columns_ratio.keys():
                if not is_qty_clm(k, header_row, table_header):
                    non_qty_clms.append(k)

            if non_qty_clms != list(columns_ratio.keys()):   # quantity_keyword detected
                for clm in non_qty_clms:
                    if clm in columns_ratio:
                        columns_ratio.pop(clm)
                quantity_column = max(columns_ratio.items(), key=operator.itemgetter(1))[0]
                suggested_quantity_column = quantity_column

            # elif non_qty_clms == list(columns_ratio.keys()):   # quantity_keyword not detected
            #     quantity_column = False
        if not quantity_column and columns_ratio.__len__() > 1 and sum(columns_ratio.values()) > 0:
            _columns_ratio = columns_ratio.copy()
            highest_ratio = max(_columns_ratio.items(), key=operator.itemgetter(1))
            _columns_ratio.pop(highest_ratio[0])
            second_highest_ratio = max(_columns_ratio.items(), key=operator.itemgetter(1))
            hr_sum = sum([string_quantity_to_integer(elt) for elt in df[highest_ratio[0]] if is_integer(elt)])
            shr_sum = sum([string_quantity_to_integer(elt) for elt in df[second_highest_ratio[0]] if is_integer(elt)])
            suggested_quantity_column = highest_ratio[0] if (abs(hr_sum) > abs(shr_sum)) else second_highest_ratio[0]

        if not columns_ratio or sum(columns_ratio.values()) == 0:
            quantity_column = False
            suggested_quantity_column = False

        return quantity_column, suggested_quantity_column
    except Exception:
        traceback.print_exc()
        return False


def get_part_number_column(df, table_header, brand_name_column, quantity_column, PART_NUMBERS):
    try:
        def item_clm_index(header_row, column_names):
            global item_number_keywords
            for index, clm in enumerate(header_row):
                if any(elt in str(clm).lower() for elt in item_number_keywords):
                    return True, column_names[index]
            return False, None

        header_row = None
        if table_header["status"]:
            if table_header["row_number"] != -1:
                header_row = df.iloc[table_header["row_number"]]
                df = df[table_header["row_number"]+1:]
            else:
                header_row = pd.Series(df.columns)

        columns_ratio = {}
        for column in df.columns:
            unique_elements = set(list(map(clean_part_number, [elt for elt in df[column].values if elt and elt == elt])))
            if not unique_elements:
                continue
            columns_ratio[column] = len(PART_NUMBERS.intersection(unique_elements)) / (df.shape[0] / len(unique_elements))

        non_part_number_clms = []   # just to avoid Error: "called before assignment"
        if brand_name_column:
            non_part_number_clms.append(brand_name_column)
        if quantity_column:
            non_part_number_clms.append(quantity_column)

        if table_header["status"]:
            item_clm_exist, item_clm_name = item_clm_index(header_row, df.columns)
            if item_clm_exist:
                non_part_number_clms.append(item_clm_name)

            for clm in non_part_number_clms:
                if clm in columns_ratio:
                    columns_ratio.pop(clm)

        if not columns_ratio or sum(columns_ratio.values()) == 0:
            return False
        return max(columns_ratio.items(), key=operator.itemgetter(1))[0]
    except Exception:
        traceback.print_exc()
        return False
# --------------------------------------------------


# Detect patter for brand_name and part_number in same column
def check_existing_patterns(df, table_header, brand_name_column, part_number_column,
                            BRAND_NAMES, BRAND_ALIASES, PART_NUMBERS):
    obn, opn = brand_name_column, part_number_column

    pattern_splitters = ["#", "(", "/"]
    brands = BRAND_NAMES.union(BRAND_ALIASES)
    if table_header["status"]:
        if table_header["row_number"] != -1:
            df = df[table_header["row_number"] + 1:]

    spltr_ratios_sample = {"b#p": 0,  "p#b": 0,  "b(p": 0, "p(b": 0,  "b/p": 0, "p/b": 0}
    column_pattern_ratios = dict((k,  spltr_ratios_sample.copy()) for k in df.columns.values)
    column_ratios = dict.fromkeys(df.columns.values, 0)

    for splitter in pattern_splitters:
        for clm in df.columns.values:
            for row in df[clm].values:
                if len(str(row).split(splitter)) == 2:
                    row_splits = str(row).split(splitter)
                    # brand_name <--splitter--> part_number
                    if brands.intersection({clean_brand_name(row_splits[0])}) or \
                            PART_NUMBERS.intersection({clean_part_number(row_splits[1])}):
                        column_pattern_ratios[clm]["b" + splitter + "p"] += 1
                        column_ratios[clm] += 1
                    elif brands.intersection({clean_brand_name(row_splits[1])}) or \
                            PART_NUMBERS.intersection({clean_part_number(row_splits[0])}):
                        column_pattern_ratios[clm]["p" + splitter + "b"] += 1
                        column_ratios[clm] += 1

    best_column = max(column_ratios.items(), key=operator.itemgetter(1))[0] if\
        sum(column_ratios.values()) is not 0 else ""
    best_pattern = max(column_pattern_ratios[best_column].items(), key=operator.itemgetter(1))[0] if\
        best_column else ""

    if not best_column and not best_pattern:
        if obn or opn:
            return obn, opn
        return False, False

    # verify final results for closing bracket ")"
    brand_name_column = part_number_column = {"column": best_column, "pattern": best_pattern}
    return brand_name_column, part_number_column


def get_brand_name_part_number_with_pattern(row, brand_name_column, part_number_column):
    extracted_brand_name, extracted_part_number = "", ""
    if not brand_name_column["column"]:
        return extracted_brand_name, extracted_part_number

    splitter = str(brand_name_column["pattern"]).replace("b",  "").replace("p",  "")
    row_splits = str(row[brand_name_column["column"]]).split(splitter)
    if row_splits.__len__() == 2:
        if str(brand_name_column["pattern"]).strip() == "b" + splitter + "p":
            extracted_brand_name = row_splits[0]
            extracted_part_number = row_splits[1]
        elif str(brand_name_column["pattern"]).strip() == "p" + splitter + "b":
            extracted_brand_name = row_splits[1]
            extracted_part_number = row_splits[0]

    return extracted_brand_name.replace(")", ""), extracted_part_number
# --------------------------------------------------


# Split brand_name and part_number from mixed column
def try_search_with_splitter(df, table_header, BRAND_NAMES, BRAND_ALIASES, PART_NUMBERS):
    try:
        global possible_splitter
        brands = BRAND_NAMES.union(BRAND_ALIASES)

        header_row = None
        if table_header["status"]:
            if table_header["row_number"] != -1:
                header_row = df.iloc[table_header["row_number"]]
                df = df[table_header["row_number"] + 1:]
            else:
                header_row = pd.Series(df.columns)

        splitter_ratios = []
        for splitter in possible_splitter:
            column_ratios = dict.fromkeys(df.columns.values, 0)
            for clm in df.columns.values:
                for row in df[clm].values:
                    row_splits = [elt for elt in str(row).split(splitter) if elt and elt == elt]

                    candidate_row_splits = row_splits.copy()
                    for elt in row_splits:
                        spltrs = [s for s in possible_splitter if s in elt]
                        if spltrs:
                            for spltr in spltrs:
                                candidate_row_splits += elt.split(spltr)

                    brand_matches = brands.intersection(
                        set([x for x in list(map(clean_brand_name, candidate_row_splits)) if x]))
                    part_number_matches = PART_NUMBERS.intersection(
                        set([x for x in list(map(clean_part_number, candidate_row_splits)) if x]))

                    if brand_matches or part_number_matches:
                        column_ratios[clm] += 1

            if not column_ratios or sum(column_ratios.values()) == 0:
                splitter_ratios.append({"splitter": splitter, "column": False,  "max_matches": 0})
            else:
                cand = max(column_ratios.items(), key=operator.itemgetter(1))
                splitter_ratios.append({"splitter": splitter, "column": cand[0],  "max_matches": cand[1]})

        # check if splitter_ratios is empty
        best_match = max(splitter_ratios, key=lambda x: x["max_matches"])
        if best_match["max_matches"] is 0 or best_match["column"] is False:
            return False, False
        return best_match, best_match
    except Exception:
        traceback.print_exc()
        return False, False


def get_brand_name_part_number_with_splitter(row, brand_name_column, part_number_column,
                                             BRAND_NAMES, BRAND_ALIASES, PART_NUMBERS):
    try:
        global possible_splitter
        extracted_brand_name, extracted_part_number = "", ""
        brands = BRAND_NAMES.union(BRAND_ALIASES)
        if not type(brand_name_column) is dict and \
                not type(part_number_column) is dict:
            return extracted_brand_name, extracted_part_number

        cell = row[brand_name_column["column"]]
        splitter = brand_name_column["splitter"]
        cell_splits = [elt for elt in str(cell).split(splitter) if elt and elt == elt]

        candidate_cell_splits = cell_splits.copy()
        for elt in cell_splits:
            spltrs = [s for s in possible_splitter if s in elt]
            if spltrs:
                for spltr in spltrs:
                    candidate_cell_splits += elt.split(spltr)

        brand_matches = brands.intersection(
            set([x for x in list(map(clean_brand_name, candidate_cell_splits)) if x]))
        part_number_matches = PART_NUMBERS.intersection(
            set([x for x in list(map(clean_part_number, candidate_cell_splits)) if x]))

        extracted_brand_name = max(list(brand_matches), key=lambda x: len(x)) if brand_matches else ""
        extracted_brand_name = next(iter([elt for elt in candidate_cell_splits if
                                          clean_brand_name(elt) == extracted_brand_name]), "")

        extracted_part_number = max(list(part_number_matches), key=lambda x: len(x)) if part_number_matches else ""
        extracted_part_number = next(iter([elt for elt in candidate_cell_splits if
                                          clean_part_number(elt) == extracted_part_number]), "")

        return str(extracted_brand_name).replace(")", ""), extracted_part_number
    except Exception:
        traceback.print_exc()
        return "", ""


def try_search_with_keywords(df, table_header, brand_name_column, part_number_column, suggested_quantity_column):
    try:
        global brand_name_header_keywords
        global part_number_header_keywords
        global quantity_header_keywords

        df.columns = pd.Series([str(c) for c in df.columns])
        df = df.dropna(axis=0, how="all").drop_duplicates()
        df = df.dropna(axis=1, how="all")
        table_header = {"status": False, "row_number": None}
        sbnc, spnc, sqc = False, False, False

        #
        # Check in Header first
        df_columns = [str(elt).lower() for elt in df.columns]
        if sqc is False:
            sqc = [clm for clm in df_columns if any([kw in str(clm).lower() for kw in quantity_header_keywords])]
            sqc = sqc[0] if sqc else False

        if sbnc is False:
            sbnc = [clm for clm in df_columns if any([kw == str(clm).lower() for kw in brand_name_header_keywords])]
            sbnc = sbnc[0] if sbnc else False

        if spnc is False:
            if sbnc:
                df_columns.remove(sbnc)
            if suggested_quantity_column:
                df_columns.remove(suggested_quantity_column)

            spnc = [clm for clm in df_columns if any([kw == str(clm).lower() for kw in part_number_header_keywords])]
            spnc = spnc[0] if spnc else False

        if any([sbnc, spnc, sqc]):   # match of any element implies header is found
            table_header = {"status": True, "row_number": -1}
            brand_name_column = sbnc if not brand_name_column else brand_name_column
            part_number_column = spnc if not part_number_column else part_number_column
            suggested_quantity_column = sqc if not suggested_quantity_column else suggested_quantity_column
            return brand_name_column, part_number_column, suggested_quantity_column, table_header, df

        # # row[1][row[1] == 'P/N'].index[0]
        # If still no column found
        if not all([sbnc, spnc, sqc]):
            for row in df.iterrows():
                row_copy = row[1].copy()
                if sqc is False:
                    sqc = [elt for elt in row_copy.items() if any([kw in str(elt[1]).lower() for kw in quantity_header_keywords])]
                    sqc = sqc[0] if sqc else False

                if sbnc is False:
                    sbnc = [elt for elt in row_copy.items() if any([kw in str(elt[1]).lower() for kw in brand_name_header_keywords])]
                    sbnc = sbnc[0] if sbnc else False

                if spnc is False:
                    if sbnc and sbnc in row_copy.items():
                        row_copy = row_copy.drop(sbnc[0])   # sbnc is a tuple while row is a pandas series
                    if sqc and sqc in row_copy.items():
                        row_copy = row_copy.drop(sqc[0])

                    spnc = [elt for elt in row_copy.items() if any([kw in str(elt[1]).lower() for kw in part_number_header_keywords])]
                    spnc = spnc[0] if spnc else False

                if any([sbnc, spnc, sqc]):  # match of any element implies header is found
                    table_header = {"status": True, "row_number": row[0]}
                    df = df[row[0]+1:]

                    # sbnc = row_copy[row_copy == sbnc[1]].index[0] if sbnc else False
                    sbnc = sbnc[0] if sbnc else False
                    brand_name_column = sbnc if not brand_name_column else brand_name_column

                    # spnc = row_copy[row_copy == spnc[1]].index[0] if spnc else False
                    spnc = spnc[0] if spnc else False
                    part_number_column = spnc if not part_number_column else part_number_column

                    # sqc = row_copy[row_copy == sqc[1]].index[0] if sqc else False
                    sqc = sqc[0] if sqc else False
                    suggested_quantity_column = sqc if not suggested_quantity_column else suggested_quantity_column
                    return brand_name_column, part_number_column, suggested_quantity_column, table_header, df

        return brand_name_column, part_number_column, suggested_quantity_column, table_header, df
    except Exception:
        traceback.print_exc()
        return brand_name_column, part_number_column, suggested_quantity_column, table_header, df


# --------------------------------------------------------------------------------
def get_row_match(row, brand_name_column, quantity_column, part_number_column,
                  BRAND_NAMES, BRAND_ALIASES, BRAND_NAME_TO_ID, BRAND_ALIAS_TO_ID,
                  PART_NUMBERS, PART_NUMBER_TO_ID):
    match = dict()
    # #################
    # GET PART_NUMBER
    # #################
    part_number_object = ""
    extracted_part_id,  extracted_part_number = "",  ""
    if part_number_column and type(part_number_column) in [int, str]:
        part_number = PART_NUMBERS.intersection({clean_part_number(row[part_number_column])})
        if part_number:
            part_number_object = PART_NUMBER_TO_ID[list(part_number)[0]]

        extracted_part_id = part_number_object["id"] if part_number_object else ""
        extracted_part_number = row[part_number_column] if part_number_column else ""

    # ##############
    # GET BRAND_NAME
    # ##############
    brand_name_object = ""
    extracted_brand_id, extracted_brand_name = "", ""
    if brand_name_column and type(brand_name_column) in [int, str]:
        brand_name = BRAND_NAMES.intersection({clean_brand_name(row[brand_name_column])})
        if brand_name:
            brand_name_object = BRAND_NAME_TO_ID[list(brand_name)[0]]
        else:
            brand_name = BRAND_ALIASES.intersection({clean_brand_name(row[brand_name_column])})
            if brand_name:
                brand_name_object = BRAND_ALIAS_TO_ID[list(brand_name)[0]]

        extracted_brand_id = brand_name_object["id"] if brand_name_object else ""
        extracted_brand_name = row[brand_name_column] if brand_name_column else ""

    # Pattern recognized or got matches from mixed columns
    if brand_name_column and part_number_column and \
            type(brand_name_column) is dict and \
            type(part_number_column) is dict:
        if "pattern" in brand_name_column:
            extracted_brand_name, extracted_part_number = get_brand_name_part_number_with_pattern(
                row,
                brand_name_column,
                part_number_column)
        else:
            extracted_brand_name, extracted_part_number = get_brand_name_part_number_with_splitter(row,
                                                                                                   brand_name_column,
                                                                                                   part_number_column,
                                                                                                   BRAND_NAMES,
                                                                                                   BRAND_ALIASES,
                                                                                                   PART_NUMBERS)
        # Extract part_number_id
        if extracted_part_number and clean_part_number(extracted_part_number) in PART_NUMBERS:
            part_number_object = PART_NUMBER_TO_ID[clean_part_number(extracted_part_number)]
            extracted_part_id = part_number_object["id"] if part_number_object else ""

        # Extract brand_name_id
        if extracted_brand_name and clean_brand_name(extracted_brand_name) in BRAND_NAMES:
            brand_name_object = BRAND_NAME_TO_ID[clean_brand_name(extracted_brand_name)]
            extracted_brand_id = brand_name_object["id"] if brand_name_object else ""

        elif extracted_brand_name and clean_brand_name(extracted_brand_name) in BRAND_ALIASES:
            brand_name_object = BRAND_ALIAS_TO_ID[clean_brand_name(extracted_brand_name)]
            extracted_brand_id = brand_name_object["id"] if brand_name_object else ""

    elif type(brand_name_column) is dict or \
            type(part_number_column) is dict:
        print("problematic row in get_row_match:", row)

    # ############
    # GET QUANTITY
    # ############
    quantity = 0
    suggested_quantity = 0
    if quantity_column or (quantity_column is 0 and type(quantity_column) != bool):
        quantity = string_quantity_to_integer(row[quantity_column]) \
            if string_quantity_to_integer(row[quantity_column]) else row[quantity_column]
        quantity = quantity if quantity == quantity else 0   # remove nan

    if suggested_quantity or (suggested_quantity is 0 and type(suggested_quantity) != bool):
        suggested_quantity = string_quantity_to_integer(row["Suggested Quantity"]) \
            if string_quantity_to_integer(row["Suggested Quantity"]) else 0

    extracted_brand_name = extracted_brand_name.replace(")", "") if \
        "(" not in extracted_brand_name else extracted_brand_name

    match = {"quantity": abs(quantity) if type(quantity) in [int, float] else quantity,
             'suggested_quantity': abs(suggested_quantity) if type(suggested_quantity) in [int, float] else suggested_quantity,
             "brand_id": extracted_brand_id,
             "brand_name": extracted_brand_name,
             "part_number_id": extracted_part_id,
             "part_number": extracted_part_number
             }
    return match
