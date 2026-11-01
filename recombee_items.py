import os
import re
import pandas as pd
from recombee_api_client.api_client import RecombeeClient, Region
from recombee_api_client.api_requests import SetItemValues, Batch
from recombee_api_client.exceptions import APIException

DB_NAME = 'mateidragusin-dev'
PRIVATE_TOKEN = os.environ['RECOMBEE_TOKEN']
REGION = Region.EU_WEST

client = RecombeeClient(DB_NAME, PRIVATE_TOKEN, region=REGION)

PATH_DATASET = 'imdb_top_1000.csv'

BATCH_SIZE = 100


def to_int(value):
    if pd.isna(value):
        return None
    cleaned = re.sub(r'[^\d]', '', str(value))
    return int(cleaned) if cleaned else None


def to_float(value):
    if pd.isna(value):
        return None
    try:
        return float(value)
    except ValueError:
        return None


def row_to_properties(row):
    properties = {
        "title": str(row['Series_Title']),
        "released_year": to_int(row['Released_Year']) if re.fullmatch(r'\d{4}', str(row['Released_Year'])) else None,
        "runtime": to_int(row['Runtime']),
        "genre": [g.strip() for g in str(row['Genre']).split(',') if g.strip()] if pd.notna(row['Genre']) else None,
        "imdb_rating": to_float(row['IMDB_Rating']),
        "meta_score": to_float(row['Meta_score']),
        "no_of_votes": to_int(row['No_of_Votes']),
        "director": str(row['Director']) if pd.notna(row['Director']) else None,
        "overview": str(row['Overview']) if pd.notna(row['Overview']) else None,
        "gross": to_int(row['Gross']),
    }
    return {k: v for k, v in properties.items() if v is not None}


def send_batch(requests):
    responses = client.send(Batch(requests))
    errors = [r for r in responses if not 200 <= int(r['code']) < 300]
    for err in errors:
        print(f"Eroare in lot: {err}")
    return len(requests) - len(errors)


def send_items():
    """Functie care citeste dataset-ul si trimite item-urile in Recombee"""
    df = pd.read_csv(PATH_DATASET)
    print(f"Se trimit {len(df)} item-uri in Recombee...")

    requests = []
    sent = 0

    for index, row in df.iterrows():
        item_id = str(index)
        properties = row_to_properties(row)

        # Adaugam request-ul de setare a valorilor pentru item
        # (SetItemValues creează automat item-ul dacă acesta nu există)
        requests.append(SetItemValues(item_id, properties, cascade_create=True))

        # Trimitem in loturi (batch) de cate 100 pentru eficienta
        if len(requests) == BATCH_SIZE:
            sent += send_batch(requests)
            requests = []
            print(f"S-a trimis un lot de {BATCH_SIZE} item-uri... ({sent}/{len(df)})")

    # Trimitem si restul ramanase (daca numarul total nu e multiplu de 100)
    if requests:
        sent += send_batch(requests)
        print("S-a trimis ultimul lot de item-uri.")

    print(f"Gata! {sent}/{len(df)} item-uri trimise cu succes.")


if __name__ == "__main__":
    try:
        send_items()
    except APIException as e:
        print(f"Eroare API Recombee: {e}")
