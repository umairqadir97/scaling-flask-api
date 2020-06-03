from cleanco import cleanco
import re
import json
import requests
import operator
try:
    from src.config import *
    from src.api_helper import clean_part_number, remove_punctuations
except:
    from config import *
    from api_helper import clean_part_number, remove_punctuations


def get_all_brands_names():
    brand_names = list()
    brand_aliases = list()
    brand_name_to_id = dict()
    brand_alias_to_id = dict()
    counter = 0  # crawling will start from index=1
    print("Extracting brands....")
    while True:
        counter += 1
        print("page=", counter)
        current_url = BRAND_DETAIL_URL.format(i=counter)
        r = requests.get(current_url)
        try:
            if r.json()["code"] == 200 and r.json()["data"]:
                for elt in r.json()["data"]:
                    cleaned_brand_name = remove_punctuations(cleanco(str(elt["brand_name"])).clean_name())
                    if cleaned_brand_name:
                        brand_names.append(cleaned_brand_name)
                        brand_name_to_id[cleaned_brand_name] = elt
                    cleaned_brand_alias = remove_punctuations(cleanco(str(elt["brand_alias"])).clean_name())
                    if cleaned_brand_alias:
                        brand_aliases.append(cleaned_brand_alias)
                        brand_alias_to_id[cleaned_brand_alias] = elt
                continue
            break
        except Exception as e:
            print("Error ({}) Processing URL: {}".format(e, current_url))

    with open('./data/outputs/brand_names.txt', 'w') as fp:
        for bn in set(sorted(brand_names, reverse=False)):
            fp.write(bn + "\n")

    with open('./data/outputs/brand_aliases.txt', 'w') as fp:
        for ba in set(sorted(brand_aliases, reverse=False)):
            fp.write(ba + "\n")

    with open("./data/outputs/brand_name_to_id.json", "w") as fp:
        json.dump(brand_name_to_id, fp)

    with open("./data/outputs/brand_alias_to_id.json", "w") as fp:
        json.dump(brand_alias_to_id, fp)

    print("Fetched total {} brands and {} aliases".format(len(brand_names), len(brand_aliases)))
    return set(brand_names), brand_name_to_id, set(brand_aliases), brand_alias_to_id


def get_all_part_numbers():
    part_numbers = list()
    part_number_to_id = dict()
    counter = 0  # crawling will start from index=1
    print("Extracting part numbers....")
    while True:
        counter += 1
        # if counter > 5:
        #     break
        print("page=", counter)
        current_url = PART_NUMBER_DETAIL_URL.format(i=counter)
        r = requests.get(current_url)
        try:
            if r.json()["code"] == 200 and r.json()["data"]:
                for elt in r.json()["data"]:
                    cleaned_part_number = clean_part_number(elt["part_number"])
                    part_numbers.append(cleaned_part_number)
                    part_number_to_id[cleaned_part_number] = elt
                continue
            break
        except Exception as e:
            print("Error ({}) Processing URL: {}".format(e, current_url))

    with open('./data/outputs/part_numbers.txt', 'w') as fp:
        for pn in part_numbers:
            fp.write(pn + "\n")

    with open("./data/outputs/part_number_to_id.json", "w") as fp:
        json.dump(part_number_to_id, fp)

    print("Fetched total {} part_numbers".format(len(part_numbers)))
    return set(part_numbers), part_number_to_id
