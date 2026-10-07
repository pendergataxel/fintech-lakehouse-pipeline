# Fintech Funds Transfer Pipeline

[![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED?logo=docker&logoColor=white)](#)
[![Apache Airflow](https://img.shields.io/badge/Apache%20Airflow-2.x-017CEE?logo=apacheairflow&logoColor=white)](#)
[![DuckDB](https://img.shields.io/badge/DuckDB-Embedded%20OLAP-FFF000?logo=duckdb&logoColor=black)](#)
[![MotherDuck](https://img.shields.io/badge/MotherDuck-Cloud%20Data%20Warehouse-FFAA00)](#)
[![Pydantic](https://img.shields.io/badge/Pydantic-Data%20Validation-E92063?logo=pydantic&logoColor=white)](#)
[![Streamlit](https://img.shields.io/badge/Streamlit-Analytics%20Dashboard-FF4B4B?logo=streamlit&logoColor=white)](#)
[![Plotly](https://img.shields.io/badge/Plotly-Interactive%20Visualizations-3F4F75?logo=plotly&logoColor=white)](#)

An end-to-end, data engineering pipeline that simulates Philippine fintech funds transfers, enforces strict schema validation and anomaly quarantining, orchestrates automated batch processing with Apache Airflow, and syncs analytical metrics to MotherDuck and an interactive Streamlit / Plotly dashboard.

---

## Overview

In modern fintech platforms, handling high-throughput payment rails (e.g., InstaPay, PESONet, QR Ph, cards) requires reliable orchestration, zero-downtime schema evolution, and resilient data quality gates. Missing fields, invalid currencies, circular transactions, and anomalous charges must be caught and routed before corrupting analytical downstream warehouses.

This project delivers a complete Lakehouse workflow built to address these challenges:

* **Synthetic Rail Simulation:** Generates realistic, non-uniform transaction streams reflecting real-world Philippine consumer habits, including business-day and rush-hour traffic skew, alongside automated synthetic anomaly injection.
* **Schema Enforcement & Quarantine:** Employs Pydantic data contracts at the ingestion boundary to validate transaction integrity, segregating clean records from malformed transactions.
* **Orchestrated Batch Processing:** Uses a containerized Apache Airflow scheduler to execute scheduled batch extraction, transformation, and analytical aggregation runs with automated retry policies.
* **Hybrid Embedded & Cloud Storage:** Leverages MotherDuck for cloud-based data warehousing.
* **Business Intelligence Serving:** Surfaces real-time transactional metrics, hourly payment rail volumes via a Streamlit dashboard.

---

## Architecture & Data Flow

An automated pipeline that simulates fintech transfer batches, validates records against business rules with Pydantic, separates malformed records into a dead-letter queue, archives original files, and syncs clean data directly into MotherDuck.

```text
       [ Synthetic Stream Generator ]
             (generate_data.py)
                      │
                      ▼
               [ Raw Landing ]
               data/raw/*.json
                      │
                      ▼
            [ ETL & Data Engine ]
                (pipeline.py)
                      │
         ┌────────────┼────────────┐
         │            │            │
         ▼            ▼            ▼
   [ Valid Data ]   [ Errors ]   [ Archive ]
   MotherDuck (Cloud) data/dlq/  data/processed/
   (Clean records)  (Failed records (Original raw files
                     with reasons)   moved here)
         │
         ▼
   [ Serving Layer ]
  Streamlit Dashboard
```

---

## Pipeline Components & Engineering Highlights

### 1. Realistic Synthetic Data Generation (`generate_data.py`)
Rather than creating completely uniform, unrealistic random data, the generator models true-to-life consumer payment habits:
* **Payment Rail Weighting:** Allocates market-realistic volume shares across Philippine rails (`instapay`: 45%, `card`: 30%, `qr_ph`: 20%, `pesonet`: 5%).
* **Temporal Skew (Days & Hours):** Biases transactions toward weekdays (80/20 weekday-to-weekend ratio) and peaks during morning, lunch, and dinner rush hours while tapering off overnight.
* **Controlled Anomaly Injection:** Deliberately injects malformed transactions to test quality boundaries (e.g., negative fees, circular self-transfers, unsupported currencies, and rogue channel tags like `crypto_token`).

### 2. Schema Contracts & Data Quality (`models/` & `pipeline.py`)
Incoming payloads are checked before any data reaches the analytical database:
* **Pydantic Validation Models:** Enforces data types, string formatting, positive transfer values, and business rules (e.g., ensuring `source_account_id != destination_account_id`).
* **Dead-Letter Queue (DLQ):** Prevents bad records from failing the whole batch. Invalid rows are caught, paired with descriptive error messages, and written to `data/dlq/` for debugging.
* **Idempotent File Handling:** Moves processed files from `data/raw/` to `data/processed/` only after successful database commits and error dumps, ensuring runs can safely re-trigger without double-counting records.

### 3. Workflow Orchestration (`dags/`)
* **Apache Airflow DAG:** Manages the sequential pipeline tasks on an automated schedule:
  ```text
  generate_transactions >> run_etl_pipeline

---

## Future Improvements & Roadmap

* **Cloud VM Deployment (AWS EC2 / GCP Compute Engine):**  
  * Transition orchestration from local Docker Desktop to an always-on cloud instance (e.g., an AWS EC2 `t3.medium` running Ubuntu and Docker Compose).

* **Automated DLQ Remediation & Alerting:**  
  * **Error Categorization:** Classify dead-letter records into recoverable errors (e.g., transient network/schema formatting) versus fatal business rule violations (e.g., negative fees, circular self-transfers).
  * **Automated Retry Pipeline:** Implement a secondary DAG or re-ingestion script to automatically reprocess quarantined payloads once schemas or reference data are updated.

* **Storage Evolution (Object Storage Landing):**  
  * Replace the local filesystem (`data/raw/`, `data/processed/`, `data/dlq/`) with an S3 or Google Cloud Storage bucket layer, making the ingestion and quarantine steps completely stateless.

---

## Acknowledgements & References

* Based on foundational pipeline concepts and workshop materials from [Python Philippines | Alysson Alvaran](https://github.com/alyssonalvaran/simple-data-lakehouse-workshop), originally shared under the [MIT License].

* Extended and modified to implement realistic transaction data generation, Dockerized orchestration, MotherDuck cloud storage, quarantine routing (DLQ capture for invalid records), and an interactive analytics dashboard.