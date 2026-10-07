from datetime import datetime, timedelta
from airflow.decorators import dag, task
import subprocess

default_args = {
    'owner': 'axel',
    'depends_on_past': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=2),
}

@dag(
    dag_id='fintech_funds_transfer_pipeline',
    default_args=default_args,
    description='Automated pipeline for synthetic transactions generation and ETL processing',
    schedule_interval='*/15 * * * *',
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=['fintech', 'duckdb', 'etl', 'transaction'],
)

def fintech_dag():

    @task
    def generate_transactions():
        # runs generate_data.py to create the synthetic records
        subprocess.run(["python", "/opt/airflow/generate_data.py"], check=True)

    @task
    def run_etl_pipeline():
        # runs pipeline.py to load verified data into motherduck
        res = subprocess.run(
            ["python", "/opt/airflow/pipeline.py"],
            cwd="/opt/airflow",
            capture_output=True,
            text=True
        )
        print('------- STDOUT -------')
        print(res.stdout)
        if res.returncode != 0:
            print('------- STDERR -------')
            print(res.stderr)
            raise RuntimeError(f"pipeline.py failed with exit code {res.returncode}:\n{res.stderr}")

    # execution order
    generate_transactions() >> run_etl_pipeline()

fintech_dag()