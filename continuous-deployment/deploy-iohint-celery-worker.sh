# Do not rely on PATH in this script; we don't really trust our caller, the flask user, which has the ability to
# run this script with any environment variables it wants.

/usr/bin/docker login -u "$DOCKER_USER" -p "$DOCKER_PASS" docker.citr.ous.ca
/usr/bin/docker pull docker.citr.ous.ca/iohint-celery-worker:latest

# task executer (celery worker)
/usr/bin/docker stop iohint-celery-worker
/usr/bin/docker rm iohint-celery-worker
/usr/bin/docker create \
  --name iohint-celery-worker \
  --net iohint-net \
  -e "SECRET_KEY=${IOHINT_SECRET_KEY}" \
  -e "DATABASE_URL=postgres://iohint@iohint-pgsql:5432/iohint" \
  -e "CELERY_BROKER_URL=amqp://guest:guest@iohint-rabbitmq:5672//" \
  docker.citr.ous.ca/iohint-celery-worker:latest
/usr/bin/docker start iohint-celery-worker
