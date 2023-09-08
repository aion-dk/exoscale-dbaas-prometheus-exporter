# Exoscale DBaaS Metrics Exporter

This Python application fetches metrics from Exoscale Database as a Service (DBaaS) and exposes them in Prometheus format. You can use this exporter to monitor multiple Exoscale DBaaS instances.

## Build Docker Image
To build the Docker image for the exporter, run the following command:
```
docker build -t dbaas-prometheus-exporter .
```

## Run the Exporter
You can run the Exoscale DBaaS Metrics Exporter using the following Docker command:
```
docker run -e exoscale_key=<YOUR_API_KEY> -e exoscale_secret=<YOUR_API_SECRET> -e database_names="<DATABASE_NAMES>" -p 8080:8080 dbaas-prometheus-exporter
```
* Replace <YOUR_API_KEY> and <YOUR_API_SECRET> with your Exoscale API key and secret.
* Replace <DATABASE_NAMES> with a comma-separated list of the database names you want to monitor.

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
