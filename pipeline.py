import pandas as pd
import logging
from typing import List, Dict, Any
import json
import duckdb
from pydantic import ValidationError
from models.transactions import FundTransferEvent

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Pull json file
def load_raw_transactions(file_path: str) -> List[Dict[str, Any]]:
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logging.error(f'Could not find {file_path}.')
        return []

# Run through schema validation
def validate_transactions(raw_transactions: List[Dict[str, Any]]) -> List[FundTransferEvent]:
    valid_transactions = []

    for transaction in raw_transactions:
        try:
            validated_transaction = FundTransferEvent(**transaction)
            valid_transactions.append(validated_transaction)
        except ValidationError as e:
            logging.warning(f"Validation failed for transaction {transaction.get('transaction_id', 'UNKNOWN')}: {e.errors()[0]['msg']}")
    return valid_transactions


# Load validated events to duckdb
def load_to_duckdb(transactions: List[FundTransferEvent], db_path: str = ':memory:') -> duckdb.DuckDBPyConnection:
    conn = duckdb.connect(db_path)

    raw_list = [transaction.model_dump() for transaction in transactions]

    if raw_list:
        validated_data = pd.DataFrame(raw_list)

        conn.execute('CREATE TABLE transfers AS SELECT * FROM validated_data')
        logging.info(f'Successfully loaded {len(validated_data)} records into DuckDB.')
    else:
        logging.warning('No valid data to load into DuckDB.')

    return conn

# MAIN FUNCTION

def main() -> None:

    file_path = 'data/raw_events.json'

    logging.info('Starting data pipeline...')
    raw_transactions = load_raw_transactions(file_path)

    logging.info(f'Loaded {len(raw_transactions)} records. Starting validation...')
    validated_transactions = validate_transactions(raw_transactions)

    logging.info('Loading validated transactions into DuckDB...')
    conn = load_to_duckdb(validated_transactions)

    print("\n--- Analytics Sample: Fund Transfers by Channels ---")
    query_result = conn.execute(
        "SELECT channel, COUNT(*) as transfer_count FROM transfers GROUP BY channel ORDER BY transfer_count DESC"
    ).fetchdf()
    
    print(query_result)

    conn.close()

if __name__ == "__main__":
    main()