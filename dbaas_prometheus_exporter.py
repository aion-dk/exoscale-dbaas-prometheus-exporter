import time
import os
import logging
import json
from exoscale.api.v2 import Client
from threading import Thread
from prometheus_client import start_http_server, Gauge

# Constants
SLEEP_INTERVAL = 30

# Get the log level from the environment variable (default to ERROR if not set)
log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()

# Configure logging
logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Set your API keys and secrets as environment variables
api_key = os.environ.get('exoscale_key')
api_secret = os.environ.get('exoscale_secret')

# Database name to scrape
database_names_str = os.environ.get('database_names')

# Zone the database lives in
database_zone = os.environ.get('database_zone', 'ch-gva-2')

# Period parameter for the request
metrics_period = os.environ.get('metrics_period', 'hour')

# Check if the environment variables are set
if api_key is None or api_secret is None or api_key == "" or api_secret == "":
    logger.error("Error: Please set the 'exoscale_key' and 'exoscale_secret' environment variables.")
    exit(1)

# Create an authentication object
exo = Client(api_key, api_secret, zone=database_zone)


logger.info(f"Info: Zone is set to {database_zone}.")
logger.info(f"Info: Period is set to {metrics_period}.")

# Define Prometheus gauge metrics for each metric with a 'database' label
dbaas_metrics = {
    'disk_usage': Gauge('dbaas_disk_usage', 'Disk space usage percentage', ['database']),
    'load_average': Gauge('dbaas_load_average', 'Load average (5 min)', ['database']),
    'mem_usage': Gauge('dbaas_memory_usage', 'Memory usage percentage', ['database']),
    'diskio_writes': Gauge('dbaas_disk_io_writes', 'Disk IOPS (writes)', ['database']),
    'mem_available': Gauge('dbaas_memory_available', 'Memory available percentage', ['database']),
    'cpu_usage': Gauge('dbaas_cpu_usage', 'CPU usage percentage', ['database']),
    'diskio_read': Gauge('dbaas_disk_io_reads', 'Disk IOPS (reads)', ['database']),
    'net_send': Gauge('dbaas_network_transmit_bytes_per_sec', 'Network transmit (bytes/s)', ['database']),
    'net_receive': Gauge('dbaas_network_receive_bytes_per_sec', 'Network receive (bytes/s)', ['database']),
}

def get_database_names():
    # If static database names are provided as an environment variable
    if database_names_str and database_names_str.strip():
        logger.debug(f"DEBUG: databases: database_names_str.split(',')")
        return database_names_str.split(',')
    else:
        # Get list of databases
        data = exo.list_dbaas_services()
        if 'dbaas-services' in data:
            # Extract the names using a list comprehension
            db_names = [db.get('name') for db in data['dbaas-services']]
            logger.debug(f"DEBUG: Retrieved dynamic database list: {db_names}")
            return db_names
        else:
            logger.error(f"ERROR: Unexpected response format from Exoscale API: {data}")
            return []

def fetch_metrics():
    while True:
        try:
            # Get the latest database names
            current_database_names = get_database_names()

            for database_name in current_database_names:
                response = exo.get_dbaas_service_metrics(
                    service_name=database_name,
                    period=metrics_period
                )
                if 'metrics' in response:
                    metrics = response['metrics']

                    # Extract the latest metric data for each metric
                    for metric_name, metric_gauge in dbaas_metrics.items():
                        latest_value = metrics[metric_name]['data']['rows'][-1][1]
                        metric_gauge.labels(database=database_name).set(latest_value)

                    logger.info(f"Info: Metrics for {database_name} have been scraped")

                elif 'message' in response:
                    logger.error(f"Error: Failed to fetch metrics for {database_name}: {response['message']}")

                else:
                    logger.error(f"Error: Failed to fetch metrics for {database_name}: unknown error")

        except Exception as e:
            logger.error(f"Error: An error occurred: {str(e)}")

        # Sleep for some time before fetching metrics again
        time.sleep(SLEEP_INTERVAL)

if __name__ == '__main__':
    # Start an HTTP server to expose the metrics
    start_http_server(8080)

    # Fetch and update metrics
    fetch_metrics()