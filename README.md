# Exoscale DBaaS Metrics Exporter

The Exoscale DBaaS Metrics Exporter is a Python application designed to fetch metrics from Exoscale Database as a Service (DBaaS) and expose them in Prometheus format.
With this exporter, you can monitor multiple Exoscale DBaaS instances. 

## Build Docker Image
To build the Docker image for the exporter, run the following command:
```
docker build -t dbaas-prometheus-exporter .
```

## Run the Exporter
You can run the Exoscale DBaaS Metrics Exporter using the following Docker command:
```
docker run -e exoscale_key=<YOUR_API_KEY> -e exoscale_secret=<YOUR_API_SECRET> -e database_names="<DATABASE_NAMES>" -e database_zone="<DATABASE_ZONE>" -e metrics_period="<METRICS_PERIOD>" -p 8080:8080 dbaas-prometheus-exporter
```
Replace the following placeholders:
* <YOUR_API_KEY> and <YOUR_API_SECRET> with your Exoscale API key and secret.

The following parameters are optional:
* <DATABASE_ZONE>: Set this if you want to specify the Exoscale zone where your databases are located (e.g., 'de-muc-1'). If not specified, it defaults to 'ch-gva-2'.
* <METRICS_PERIOD>: Set this if you want to specify the period for metric collection (e.g., 'hour', 'day', 'week', 'month', 'year'). If not specified, it defaults to 'hour'.
* <DATABASE_NAMES> with a comma-separated list of the database names you want to monitor. If not specified, it defaults to all databases in the zone

The exporter will start and expose Prometheus metrics on port 8080. You can configure your Prometheus server to scrape metrics from this exporter.

## Prometheus Configuration
To scrape metrics from this exporter, add the following configuration to your Prometheus prometheus.yml file:
```
scrape_configs:
  - job_name: 'dbaas-prometheus-exporter'
    static_configs:
      - targets: ['<EXPORTER_IP>:8080'] 
```
* Replace <EXPORTER_IP> with the exporter's IP address or hostname
