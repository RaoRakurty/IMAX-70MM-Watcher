FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
    && useradd --uid 10001 --no-create-home appuser
COPY watcher.py cloud_service.py state_store.py config.json ./
USER 10001
EXPOSE 8080
CMD ["python", "cloud_service.py"]
