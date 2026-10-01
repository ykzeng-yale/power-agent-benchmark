FROM gcr.io/power-agent-476822/power-agent-api@sha256:c7744480a44406e7d92189d13300458481cc91a07adb227986090bc5f0170581
COPY linux_release_regression.py replication-questions.json regression-release-manifest.json /app/
CMD ["python3", "/app/linux_release_regression.py"]
