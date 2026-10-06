import logging
from typing import List, Dict, Any, Tuple, Optional
import json
import duckdb
from pydantic import ValidationError
from models.transactions import FundTransferTransaction
from datetime import datetime, timezone
import glob
import os
import pandas as pd
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Pull json files
def load_raw_transactions(pattern: str) -> List[Dict[str, Any]]:

    matched_files = glob.glob(pattern)

    if not matched_files:
        logging.error(f'No files matched pattern: {pattern}')
        return []

    all_events = []

    for file_path in matched_files:
        try:
            with open(file_path, 'r') as f:
                records = json.load(f)
                all_events.extend(records)
                logging.info(f'Loaded {len(records)} events from {file_path}')
        except Exception as e:
            logging.error(f"Error reading {file_path}: {e}")

    return all_events

# Run through schema validation
# Route corrupted records to dlq
def validate_transactions(raw_transactions: List[Dict[str, Any]], dlq_path: Optional[str] = None) -> Tuple[List[FundTransferTransaction], int]:
    valid_transactions = []
    dead_letter_queue = []

    for transaction in raw_transactions:
        try:
            validated_transaction = FundTransferTransaction(**transaction)
            valid_transactions.append(validated_transaction)
        except ValidationError as e:

            error = {
                'dropped_at': datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                'transaction_id': transaction.get('transaction_id', 'UNKNOWN'),
                'error_reasons': [err['msg'] for err in e.errors()],
                'raw_payload': transaction
            }

            dead_letter_queue.append(error)

            logging.warning(f"Rejected transaction {transaction.get('transaction_id', 'UNKNOWN')}: {e.errors()[0]['msg']}")

    if dead_letter_queue:
        if dlq_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            dlq_path = f"data/dlq/error_log_{timestamp}.json"

        os.makedirs(os.path.dirname(dlq_path), exist_ok=True)

        with open(dlq_path, 'w') as f:
            json.dump(dead_letter_queue, f, indent=2)
        logging.info(f'Routed {len(dead_letter_queue)} bad records to "{dlq_path}".')
    
    return valid_transactions, len(dead_letter_queue)


# Load validated tansactions to motherduck
def load_to_duckdb(transactions: List[FundTransferTransaction], db_name: str = 'funds_transfer_db') -> duckdb.DuckDBPyConnection:
    conn = duckdb.connect(f'md:{db_name}')

    raw_list = [transaction.model_dump() for transaction in transactions]

    if raw_list:
        validated_data = pd.DataFrame(raw_list)

        # Update cloud database table
        conn.execute('CREATE OR REPLACE TABLE transfers AS SELECT * FROM validated_data')
        logging.info(f'Successfully loaded {len(validated_data)} records into MotherDuck cloud table "transfers".')

        # Update single local Parquet snapshot on disk
        parquet_path = Path('data/parquet/transfers').resolve()
        parquet_path.mkdir(parents=True, exist_ok=True)

        target_file = parquet_path / "transfers.parquet"

        # Write directly to disk
        validated_data.to_parquet(str(target_file), index=False)
        logging.info(f"Local Parquet snapshot overwritten at '{target_file}'.")

    else:
        logging.warning('No valid data to load into MotherDuck.')

    return conn

# MAIN FUNCTION

def main() -> None:

    file_pattern = 'data/raw/raw_transactions_*.json'

    logging.info('Starting data pipeline...')
    raw_transactions = load_raw_transactions(file_pattern)

    if not raw_transactions:
        logging.warning("Pipeline execution stopped: No raw transaction files found to process.")
        return

    logging.info(f'Loaded {len(raw_transactions)} records. Starting validation...')
    validated_transactions, dropped_count = validate_transactions(raw_transactions)
    logging.info(f'Validation complete: {len(validated_transactions)} passed, {dropped_count} sent to DLQ.')

    logging.info('Loading validated transactions into DuckDB...')
    conn = load_to_duckdb(validated_transactions)

    conn.close()
    logging.info('Pipeline finished successfully.')

if __name__ == "__main__":
    main()