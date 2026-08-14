FROM python:3.13-slim

WORKDIR /flaglet

# Copy everything to /flaglet in container
# note to self: first dir = host machine, second dir = inside container. '.' in container == WORKDIR /flaglet
COPY . .

RUN pip install -r requirements.txt

CMD ["python", "bot.py"]
