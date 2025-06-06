FROM python:3.9-slim

WORKDIR /app

COPY app.py /app/

RUN pip install flask requests

CMD ["python", "app.py"]
