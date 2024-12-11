FROM python:3.8-slim

WORKDIR /acquisiton

COPY requirements.txt requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt

ARG DEBUG_DATA_FLOW=true
ENV DEBUG_DATA_FLOW=${DEBUG_DATA_FLOW}

COPY api.py api.py

CMD ["python", "api.py"]