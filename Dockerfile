FROM python:3.10-slim-bookworm

RUN apt-get update && apt-get upgrade -y && apt-get install -y git

COPY requirements.txt /requirements.txt
RUN pip install -U pip && pip install -U -r requirements.txt

WORKDIR /PronWaliZoneBot
COPY . /PronWaliZoneBot

# startup script add karo
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

CMD ["/entrypoint.sh"]
