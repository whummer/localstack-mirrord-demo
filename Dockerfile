FROM python

RUN pip install boto3 flask requests

ADD demo/services /tmp/services

CMD ["python", "/tmp/main_service.py"]
