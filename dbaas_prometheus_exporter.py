import time
import os
import logging
from exoscale.api.v2 import Client
from prometheus_client import start_http_server, Gauge

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Set your API keys and secrets as environment variables
api_key = os.environ.get('exoscale_key')
api_secret = os.environ.get('exoscale_secret')

#database name to scrape
database_names_str = os.environ.get('database_names')

# Zone the database lives in
database_zone = os.environ.get('database_zone')

# Period parameter for the request
metrics_period = os.environ.get('metrics_period')

# Check if the environment variables are set
if api_key is None or api_secret is None or api_key == "" or api_secret == "":
    logger.error("Error: Please set the 'exoscale_key' and 'exoscale_secret' environment variables.")
    exit(1)

if database_names_str is None or database_names_str == "":
    logger.error("Error: Please set the 'database_names' environment variables.")
    exit(1)

# Explicit Zone declaration, reporting the Client defaults
if database_zone is None or database_zone == "":
    database_zone = 'ch-gva-2'
logger.info(f"Info: Zone is set to {database_zone}.")

# Set period
ALLOWED_PERIODS = {'hour', 'week', 'year', 'month', 'day'}
DEFAULT_PERIOD = 'hour'
if metrics_period is None or metrics_period == "":
    metrics_period = DEFAULT_PERIOD
if metrics_period not in ALLOWED_PERIODS:
    metrics_period = DEFAULT_PERIOD
    logger.warning(f"Warning: the 'metrics_period' environment variable is not one of {ALLOWED_PERIODS}, defaulting to '{DEFAULT_PERIOD}'.")
logger.info(f"Info: Period is set to {metrics_period}.")

#split database names
database_names = database_names_str.split(',')

# Define Prometheus gauge metrics for each metric with a 'database' label
dbaas_disk_usage = Gauge('dbaas_disk_usage', 'Disk space usage percentage', ['database'])
dbaas_load_average = Gauge('dbaas_load_average', 'Load average (5 min)', ['database'])
dbaas_mem_usage = Gauge('dbaas_memory_usage', 'Memory usage percentage', ['database'])
dbaas_diskio_writes = Gauge('dbaas_disk_io_writes', 'Disk IOPS (writes)', ['database'])
dbaas_mem_available = Gauge('dbaas_memory_available', 'Memory available percentage', ['database'])
dbaas_cpu_usage = Gauge('dbaas_cpu_usage', 'CPU usage percentage', ['database'])
dbaas_diskio_reads = Gauge('dbaas_disk_io_reads', 'Disk IOPS (reads)', ['database'])
dbaas_net_send = Gauge('dbaas_network_transmit_bytes_per_sec', 'Network transmit (bytes/s)', ['database'])
dbaas_net_receive = Gauge('dbaas_network_receive_bytes_per_sec', 'Network receive (bytes/s)', ['database'])


# Create an authentication object
exo = Client(api_key, api_secret, zone=database_zone)


def fetch_metrics(database_names):
    while True:
        try:
            for database_name in database_names:
                response = exo.get_dbaas_service_metrics(
                    service_name=database_name,
                    period=metrics_period
                )

                if 'metrics' in response:
                    metrics = response['metrics']

                    # Extract the latest metric data for each metric
                    latest_disk_usage = metrics['disk_usage']['data']['rows'][-1][1]
                    latest_load_average = metrics['load_average']['data']['rows'][-1][1]
                    latest_mem_usage = metrics['mem_usage']['data']['rows'][-1][1]
                    latest_diskio_writes = metrics['diskio_writes']['data']['rows'][-1][1]
                    latest_mem_available = metrics['mem_available']['data']['rows'][-1][1]
                    latest_cpu_usage = metrics['cpu_usage']['data']['rows'][-1][1]
                    latest_diskio_reads = metrics['diskio_read']['data']['rows'][-1][1]
                    latest_net_send = metrics['net_send']['data']['rows'][-1][1]
                    latest_net_receive = metrics['net_receive']['data']['rows'][-1][1]

                    # Set the Prometheus metrics with the latest values
                    dbaas_disk_usage.labels(database=database_name).set(latest_disk_usage)
                    dbaas_load_average.labels(database=database_name).set(latest_load_average)
                    dbaas_mem_usage.labels(database=database_name).set(latest_mem_usage)
                    dbaas_diskio_writes.labels(database=database_name).set(latest_diskio_writes)
                    dbaas_mem_available.labels(database=database_name).set(latest_mem_available)
                    dbaas_cpu_usage.labels(database=database_name).set(latest_cpu_usage)
                    dbaas_diskio_reads.labels(database=database_name).set(latest_diskio_reads)
                    dbaas_net_send.labels(database=database_name).set(latest_net_send)
                    dbaas_net_receive.labels(database=database_name).set(latest_net_receive)

                    logger.info(f"Info: Metrics for {database_name} has been scraped")

                elif 'message' in response:
                    logger.error(f"Error: Failed to fetch metrics for {database_name}: {response['message']}")

                else:
                    logger.error(f"Error: Failed to fetch metrics for {database_name}: unknown error")

        except Exception as e:
            logger.error(f"Error: An error occurred for {database_name}: {str(e)}")

        # Sleep for some time before fetching metrics again
        time.sleep(30)

if __name__ == '__main__':
    # Start an HTTP server to expose the metrics
    start_http_server(8080)

    # Fetch and update metrics
    fetch_metrics(database_names)
