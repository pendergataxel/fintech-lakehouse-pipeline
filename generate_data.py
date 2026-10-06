import json
import random
from faker import Faker
from datetime import datetime

def generate_transactions(num_records: int = 1000, error_rate: float = 0.05) -> None:
    fake = Faker()
    transactions = []
    supported_channels = ['instapay', 'pesonet', 'qr_ph', 'card']

    for i in range(num_records):
        is_error = random.random() < error_rate
        src_acc = fake.bothify("ACCN-##########")
        dest_acc = fake.bothify("ACCN-##########")
        while dest_acc == src_acc: # make sure dest and src accs generated are not the same
            dest_acc = fake.bothify("ACCN-##########")

        transaction = {
            "transaction_id": fake.uuid4(),
            "transaction_name": "funds.transfer",
            "timestamp": fake.date_time_between(start_date="-30d", end_date="now").isoformat() + "Z",
            "source_account_id": src_acc,
            "destination_account_id": src_acc if (is_error and random.random() < 0.4) else dest_acc,
            "amount": round(random.uniform(10.0, 50000.0), 2),
            "currency": fake.currency_code() if (is_error and random.random() >= 0.5) else 'PHP',
            "channel": 'crypto_token' if (is_error and random.random() <= 0.5) else random.choice(supported_channels),
            "fee": -10.00 if (is_error and random.random() > 0.4) else (10.00 if random.random() > 0.4 else None)
        }

        transactions.append(transaction)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f'data/raw/raw_transactions_{timestamp}.json'
    with open(output_path, 'w') as f:
        json.dump(transactions, f, indent=2)

    print(f"Generated {num_records} events in {output_path} (Approx {int(num_records * error_rate)} intentional errors.)")

if __name__ == "__main__":
    generate_transactions()