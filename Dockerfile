FROM python:3

WORKDIR /app

RUN pip install prometheus-client requests

COPY dbaas_prometheus_exporter.py /app/

EXPOSE 8080

CMD ["python", "dbaas_prometheus_exporter.py"]

