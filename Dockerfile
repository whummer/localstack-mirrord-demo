FROM python

RUN pip install boto3 flask requests

ADD demo/services /app/services

CMD ["python", "/app/services/main-service/service.py"]
