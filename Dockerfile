FROM python:2

RUN pip install flask requests

COPY src /src/

EXPOSE 5000

ENTRYPOINT ["python", "/src/rest.py"]


