import json
import random
from faker import Faker
from datetime import datetime, timedelta

def generate_realistic_timestamp(days_back: int = 30) -> str:
    """
    This function is used to generate realistic transaction timestamp
    It favors weekdays over weekends 80/20 split 
    and daytime, lunch, and evening rush over late-night hours
    """

    today = datetime.now()

    dates_pool = [today - timedelta(days=i) for i in range(days_back)]

    day_weights = [1.0 if d.weekday() < 5 else 0.25 for d in dates_pool]
    selected_date = random.choices(dates_pool, weights=day_weights, k=1)[0]

    # PH time
    hour_weights = [
            7, 9, 10, 10, 9, 8,    # 8am-1pm (banking, work, lunch)
            8, 7, 7,               # 2pm-4pm
            10, 9, 8, 7, 5,        # 5pm-9pm (dinner, evening peak)
            3, 2,                  # 10pm-11pm
            1, 1, 1, 1, 1, 1,      #12am-5pm (sleep)
            3, 5                    # 6am-7am (early morning start)
        ]
    
    selected_hour = random.choices(range(24), weights=hour_weights, k=1)[0]

    # assemble
    final_dt = selected_date.replace(
        hour=selected_hour,
        minute=random.randint(0, 59),
        second=random.randint(0, 59),
        microsecond=0
    )

    return final_dt.isoformat() + "Z"


def generate_transactions(num_records: int = 1000, error_rate: float = 0.05) -> None:
    fake = Faker()
    transactions = []
    supported_channels = ['instapay', 'pesonet', 'qr_ph', 'card']
    channel_weights = [0.45, 0.05, 0.20, 0.30]

    for i in range(num_records):
        is_error = random.random() < error_rate
        src_acc = fake.bothify("ACCN-##########")
        dest_acc = fake.bothify("ACCN-##########")
        while dest_acc == src_acc: # make sure dest and src accs generated are not the same
            dest_acc = fake.bothify("ACCN-##########")

        transaction = {
            "transaction_id": fake.uuid4(),
            "transaction_name": "funds.transfer",
            "timestamp": generate_realistic_timestamp(),
            "source_account_id": src_acc,
            "destination_account_id": src_acc if (is_error and random.random() < 0.4) else dest_acc,
            "amount": round(random.uniform(10.0, 50000.0), 2),
            "currency": fake.currency_code() if (is_error and random.random() >= 0.5) else 'PHP',
            "channel": 'crypto_token' if (is_error and random.random() <= 0.5) else random.choices(supported_channels, weights=channel_weights, k=1)[0],
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