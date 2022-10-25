from __future__ import unicode_literals
from flask import Flask, request, jsonify, Response
from flask import redirect, url_for, abort
from flask_cors import CORS, cross_origin
import pandas as pd
from src.api_helper import *
from src.config import *
from src.data_extractors import *
from werkzeug.utils import secure_filename


UPLOAD_FOLDER = './uploads'
ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv'}

app = Flask(__name__)
app.config['CORS_HEADERS'] = 'Content-Type'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# Global Variables
BRAND_NAMES = set(read_lines('./data/outputs/brand_names.txt')).difference(invalid_brand_names)
BRAND_ALIASES = set(read_lines('./data/outputs/brand_aliases.txt')).difference(invalid_brand_names)
PART_NUMBERS = set(read_lines('./data/outputs/part_numbers.txt')).difference(invalid_part_numbers)

BRAND_NAME_TO_ID = read_dictionary_json("./data/outputs/brand_name_to_id.json")
BRAND_ALIAS_TO_ID = read_dictionary_json("./data/outputs/brand_alias_to_id.json")
PART_NUMBER_TO_ID = read_dictionary_json("./data/outputs/part_number_to_id.json")


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/api/get-match/<int:page_id>', methods=['GET'])
@cross_origin(origin='*', headers=['Content-Type'])
def process_from_message_id(page_id):
    global BRAND_NAMES
    global BRAND_ALIASES
    global PART_NUMBERS
    global BRAND_NAME_TO_ID
    global BRAND_ALIAS_TO_ID
    global PART_NUMBER_TO_ID

    try:
        url = EMAIL_DETAIL_URL.format(i=page_id)
        try:
            tables = get_tables_from_url(url)
        except Exception as e:
            print("ERROR fetching tables:", e)
            return jsonify({"Error": "Could not fetch tables"}), 400

        matches = []
        for index, df in enumerate(tables):
            df, table_header = fix_data_frame(df, BRAND_NAMES, BRAND_ALIASES, PART_NUMBERS)
            brand_name_column = get_brand_name_column(df, table_header, BRAND_NAMES, BRAND_ALIASES)
            quantity_column, suggested_quantity_column = get_quantity_column(df, table_header)
            part_number_column = get_part_number_column(df, table_header, brand_name_column, quantity_column,
                                                        PART_NUMBERS)

            # Check Existing Patterns for brand_names and part_numbers (PN#BN, PN/BN, PN(BN)...)
            if brand_name_column is False or part_number_column is False:
                brand_name_column, part_number_column = check_existing_patterns(df, table_header, brand_name_column,
                                                                                part_number_column, BRAND_NAMES,
                                                                                BRAND_ALIASES, PART_NUMBERS)

            # Check B.N. and P.N. columns merged with others
            if brand_name_column is False and part_number_column is False:
                brand_name_column, part_number_column = try_search_with_splitter(df, table_header, BRAND_NAMES,
                                                                                 BRAND_ALIASES, PART_NUMBERS)

            # Check column header with keyword based search
            if brand_name_column is False or part_number_column is False:
                brand_name_column, part_number_column, suggested_quantity_column, table_header, df = \
                    try_search_with_keywords(df, table_header, brand_name_column, part_number_column,
                                             suggested_quantity_column)

            if table_header["status"] and not (brand_name_column or part_number_column or quantity_column):
                print("ERROR in detecting columns: mid={}, table_index={}\n".format(page_id, index))
                continue

            df["Suggested Quantity"] = 0
            if suggested_quantity_column or suggested_quantity_column is 0:  # 0 is logically False
                df["Suggested Quantity"] = df[suggested_quantity_column]
                df["Suggested Quantity"].ffill(inplace=True)

            header_crossed = False
            for row in df.iterrows():
                if not header_crossed:
                    if not any([is_integer(clm) for clm in row[1].drop(labels=["Suggested Quantity"])]):
                        if not exist_brand_alias_or_part(row[1], BRAND_NAMES, BRAND_ALIASES, PART_NUMBERS):
                            continue
                header_crossed = True
                row_match = get_row_match(row[1], brand_name_column, quantity_column, part_number_column,
                                          BRAND_NAMES, BRAND_ALIASES, BRAND_NAME_TO_ID, BRAND_ALIAS_TO_ID,
                                          PART_NUMBERS, PART_NUMBER_TO_ID)
                if not any([bool(x) for x in row_match.values()]):
                    continue
                matches.append(row_match)
        return jsonify(matches), 200
    except Exception:
        traceback.print_exc()
        return jsonify({"Error": "Can not process tables"}), 500


@app.route('/api/get-match-from-file/', methods=['POST'])
@cross_origin(origin='*', headers=['Content-Type'])
def process_from_excel():
    global BRAND_NAMES
    global BRAND_ALIASES
    global PART_NUMBERS
    global BRAND_NAME_TO_ID
    global BRAND_ALIAS_TO_ID
    global PART_NUMBER_TO_ID

    try:
        matches = []
        if not os.path.exists("./uploads"):
            os.mkdir("./uploads")

        if request.method == 'POST':
            # check if the post request has the file part
            if 'file' not in request.files:
                return jsonify({"Error": "No file part"}), 400

            file = request.files['file']
            if file.filename == '':
                return jsonify({"Error": "No file part"}), 400

            if not(file and allowed_file(file.filename)):
                return jsonify({"Error": "Invalid file type"}), 400

            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

                # LOAD DataFrame
                if filename.endswith(".xlsx") or filename.endswith(".xls"):
                    df = pd.read_excel(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                if filename.endswith(".csv"):
                    df = pd.read_csv(os.path.join(app.config['UPLOAD_FOLDER'], filename))

                matches = []
                df, table_header = fix_data_frame(df, BRAND_NAMES, BRAND_ALIASES, PART_NUMBERS)
                brand_name_column = get_brand_name_column(df, table_header, BRAND_NAMES, BRAND_ALIASES)
                quantity_column, suggested_quantity_column = get_quantity_column(df, table_header)
                part_number_column = get_part_number_column(df, table_header, brand_name_column, quantity_column,
                                                            PART_NUMBERS)

                # Check Existing Patterns for brand_names and part_numbers (PN#BN, PN/BN, PN(BN)...)
                if brand_name_column is False or part_number_column is False:
                    brand_name_column, part_number_column = check_existing_patterns(df, table_header, brand_name_column,
                                                                                    part_number_column, BRAND_NAMES,
                                                                                    BRAND_ALIASES, PART_NUMBERS)

                # Check B.N. and P.N. columns merged with others
                if brand_name_column is False and part_number_column is False:
                    brand_name_column, part_number_column = try_search_with_splitter(df, table_header, BRAND_NAMES,
                                                                                     BRAND_ALIASES, PART_NUMBERS)

                # Check column header with keyword based search
                if brand_name_column is False or part_number_column is False:
                    brand_name_column, part_number_column, suggested_quantity_column, table_header, df = \
                        try_search_with_keywords(df, table_header, brand_name_column, part_number_column,
                                                 suggested_quantity_column)

                df["Suggested Quantity"] = 0
                if suggested_quantity_column or suggested_quantity_column is 0:   # 0 is logically False
                    df["Suggested Quantity"] = df[suggested_quantity_column]
                    df["Suggested Quantity"].ffill(inplace=True)

                header_crossed = False
                for row in df.iterrows():
                    if (not header_crossed) and (not any([is_integer(clm) for clm in row[1]])) and \
                            not exist_brand_alias_or_part(row[1], BRAND_NAMES, BRAND_ALIASES, PART_NUMBERS):
                        continue
                    header_crossed = True
                    row_match = get_row_match(row[1], brand_name_column, quantity_column, part_number_column,
                                              BRAND_NAMES, BRAND_ALIASES, BRAND_NAME_TO_ID, BRAND_ALIAS_TO_ID,
                                              PART_NUMBERS, PART_NUMBER_TO_ID)
                    if not any([bool(x) for x in row_match.values()]):
                        continue
                    matches.append(row_match)

                os.system("rm ./uploads/*")   # clean uploads folder
                return jsonify(matches), 200
    except Exception:
        traceback.print_exc()
        return jsonify({"Error": "Can not process tables"}), 500


if __name__ == '__main__':
    app.run(debug=DEBUG, port=5000, host='0.0.0.0')
