FROM python:3

WORKDIR /app

COPY dbaas_prometheus_exporter.py /app/

RUN pip install prometheus-client requests

EXPOSE 8080

CMD ["python", "dbaas_prometheus_exporter.py"]

