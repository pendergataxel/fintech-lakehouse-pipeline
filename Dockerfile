FROM apache/airflow:2.9.0-python3.11

USER airflow
COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt

