FROM python:3.7-slim

WORKDIR /app
COPY requirements.txt ./
RUN pip install --trusted-host pypi.python.org -r requirements.txt

COPY model ./model
COPY static ./static
COPY templates ./templates
COPY app.py flask_reverse_proxy.py data.json weights.h5 ./

ENV PORT 5000
#CMD ["python", "./app.py"]
CMD ["gunicorn", "--threads=5", "--workers=1", "--bind=0.0.0.0:5000", "app:app" ]
