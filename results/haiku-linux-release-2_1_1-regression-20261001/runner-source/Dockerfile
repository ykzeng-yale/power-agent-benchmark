FROM gcr.io/power-agent-476822/power-agent-api@sha256:4ec7da9286998fc5eef8261f6cf80411bbcd7312e825d292c04cda642656e2fc
COPY linux_release_regression.py replication-questions.json regression-release-manifest.json /app/
CMD ["python3", "/app/linux_release_regression.py"]
