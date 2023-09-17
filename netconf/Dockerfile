FROM ubuntu.jammy
RUN apt update
RUN apt -y install python3
WORKDIR /app
COPY config.ini
COPY requirements.txt
COPY netconf/*.py netconf/
RUN apt -y install -r requirements
WORKDIR /app/netconf
CMD ["collector.py"]
ENTRYPOINT ["python3", "-u"]
