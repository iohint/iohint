iohint environment
------------------

iohint leverages Docker for consistent packaged application deployments.

Required dependencies: a RabbitMQ server, and a PostgreSQL server.

Here's a rough setup; ...secret-key... is a private random Django secret key.  Note that docker.citr.ous.ca is a private
Docker server, but, the images pushed there are built out of this repository from the circle.yml file, so they could
easily be reproduced and hosted in a public location.  (In fact... that sounds like a great idea... why am I
pushing Open Source software into a private repo?  Well, I had the private repo available... and didn't much think
about it.)

```
docker network create iohint-net

docker stop iohint-rabbitmq
docker rm iohint-rabbitmq
docker create \
  --name iohint-rabbitmq \
  --hostname iohint-rabbitmq \
  --net iohint-net \
  -v $HOME/bulk/iohint/rabbitmq:/var/lib/rabbitmq \
  rabbitmq:3.6
docker start iohint-rabbitmq

docker stop iohint-pgsql
docker rm iohint-pgsql
docker create \
  --name iohint-pgsql \
  --net iohint-net \
  -v $HOME/bulk/iohint/postgres:/var/lib/postgresql/data \
  -e "POSTGRES_USER=iohint" \
  -e "POSTGRES_DB=iohint" \
  postgres:9.6
docker start iohint-pgsql

# DB Migration Command
docker pull docker.citr.ous.ca/iohint-celery-beat:latest
docker run \
  --net iohint-net \
  -e "SECRET_KEY=...secret-key..." \
  -e "DATABASE_URL=postgres://iohint@iohint-pgsql:5432/iohint" \
  -e "CELERY_BROKER_URL=amqp://guest:guest@iohint-rabbitmq:5672//" \
  docker.citr.ous.ca/iohint-celery-beat:latest \
  ./manage.py migrate

# task executer (celery worker)
docker stop iohint-celery-worker
docker rm iohint-celery-worker
docker pull docker.citr.ous.ca/iohint-celery-worker:latest
docker create \
  --name iohint-celery-worker \
  --net iohint-net \
  -e "SECRET_KEY=...secret-key..." \
  -e "DATABASE_URL=postgres://iohint@iohint-pgsql:5432/iohint" \
  -e "CELERY_BROKER_URL=amqp://guest:guest@iohint-rabbitmq:5672//" \
  docker.citr.ous.ca/iohint-celery-worker:latest
docker start iohint-celery-worker

# scheduling process (celery beat)
docker stop iohint-celery-beat
docker rm iohint-celery-beat
docker pull docker.citr.ous.ca/iohint-celery-beat:latest
docker create \
  --name iohint-celery-beat \
  --net iohint-net \
  -e "SECRET_KEY=...secret-key..." \
  -e "DATABASE_URL=postgres://iohint@iohint-pgsql:5432/iohint" \
  -e "CELERY_BROKER_URL=amqp://guest:guest@iohint-rabbitmq:5672//" \
  docker.citr.ous.ca/iohint-celery-beat:latest
docker start iohint-celery-beat
```
