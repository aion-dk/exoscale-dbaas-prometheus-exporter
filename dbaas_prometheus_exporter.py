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

# Configure logging to output in JSON format
class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'message': record.getMessage(),
            'logger': record.name
        }
        return json.dumps(log_data)

# Set the formatter for the logger
json_formatter = JSONFormatter()

# Create a new logger
logger = logging.getLogger()
logger.setLevel(log_level)

# Create a stream handler
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(json_formatter)

# Add the stream handler to the logger
logger.addHandler(stream_handler)


# Set your API keys and secrets as environment variables
api_key = os.environ.get('exoscale_key')
api_secret = os.environ.get('exoscale_secret')

# Database name to scrape
database_names_str = os.environ.get('database_names')

database_zone = os.environ.get('database_zone')

# Period parameter for the request
metrics_period = os.environ.get('metrics_period', 'hour')

# Check if the environment variables are set
if api_key is None or api_secret is None or api_key == "" or api_secret == "":
    logger.error("Please set the 'exoscale_key' and 'exoscale_secret' environment variables.")
    exit(1)

#output if no zone is specified
if not database_zone:
    logger.info("No specific zone provided. Using all available zones.")

# Create an authentication object
exo = Client(api_key, api_secret)

logger.info(f"Period is set to {metrics_period}.")
db_names = []

# Define Prometheus gauge metrics for each metric with a 'database' label
dbaas_metrics = {
    'disk_usage': Gauge('dbaas_disk_usage', 'Disk space usage percentage', ['database','node']),
    'load_average': Gauge('dbaas_load_average', 'Load average (5 min)', ['database','node']),
    'mem_usage': Gauge('dbaas_memory_usage', 'Memory usage percentage', ['database','node']),
    'diskio_writes': Gauge('dbaas_disk_io_writes', 'Disk IOPS (writes)', ['database','node']),
    'mem_available': Gauge('dbaas_memory_available', 'Memory available percentage', ['database','node']),
    'cpu_usage': Gauge('dbaas_cpu_usage', 'CPU usage percentage', ['database','node']),
    'diskio_read': Gauge('dbaas_disk_io_reads', 'Disk IOPS (reads)', ['database','node']),
    'net_send': Gauge('dbaas_network_transmit_bytes_per_sec', 'Network transmit (bytes/s)', ['database','node']),
    'net_receive': Gauge('dbaas_network_receive_bytes_per_sec', 'Network receive (bytes/s)', ['database','node']),
}

def get_database_names():
    try:
        clients_to_query = []
        if database_zone:
            logger.info(f"Querying specific zone: {database_zone}")
            if not api_key or not api_secret:
                raise ValueError("EXOSCALE_API_KEY and EXOSCALE_API_SECRET must be set.")
            clients_to_query.append(Client(api_key, api_secret, zone=database_zone))
        else:
            logger.info("No specific zone provided. Querying all available zones.")
            clients_to_query = create_clients()
        
        for client in clients_to_query:
            logger.debug(f"Fetching services for zone: {client.zone}")
            data = client.list_dbaas_services()

            services = data.get('dbaas-service')
            if not isinstance(services, list):
                error_msg = f"API response for zone '{client.zone}' is malformed. Expected 'dbaas-services' to be a list, but got: {type(services)}. Full response: {data}"
                logger.error(error_msg)
                raise RuntimeError(error_msg)

            for db in services:
                if not isinstance(db, dict):
                    logger.warning(f"Skipping malformed item in service list: {db}")
                    continue

                db_name = db.get('name')
                if not db_name:
                    logger.warning(f"Skipping database service with no name: {db}")
                    continue
                
                db_names.append(db_name)

        logger.debug(f"Retrieved dynamic database list: {db_names}")
        return db_names
    except Exception as e:
        error_msg = f"Failed to get database names due to an unhandled exception: {e}"
        logger.error(error_msg, exc_info=True)
        raise RuntimeError(error_msg) from e

def create_clients():
    if not api_key or not api_secret:
        raise ValueError("API key and secret must be set to create clients.")
    zones_info = exo.list_zones()
    zone_names = [zone.get('name') for zone in zones_info['zones']]
    clients = []

    for zone_name in zone_names:
        client = Client(api_key, api_secret, zone=zone_name)
        clients.append(client)

    logger.debug(f"data: {clients}")
    return clients


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
                        rows = metrics[metric_name]['data']['rows']
                        latest_row = rows[-1]
                        for index in range(1, len(latest_row)):
                            latest_value = latest_row[index]
                            column_label = metrics[metric_name]['data']['cols'][index]['label']
                            if latest_value is not None:
                                metric_gauge.labels(database=database_name, node=column_label).set(latest_value)
                    logger.info(f"Metrics for {database_name} have been scraped")

                elif 'message' in response:
                    logger.error(f"Failed to fetch metrics for {database_name}: {response['message']}")

                else:
                    logger.error(f"Failed to fetch metrics for {database_name}: unknown error")

        except Exception as e:
            logger.error(f"An error occurred: {str(e)}")

        # Sleep for some time before fetching metrics again
        time.sleep(SLEEP_INTERVAL)

if __name__ == '__main__':
    # Start an HTTP server to expose the metrics
    start_http_server(8080)

    # Fetch and update metrics
    fetch_metrics()
