# Do not rely on PATH in this script; we don't really trust our caller, the flask user, which has the ability to
# run this script with any environment variables it wants.

/usr/bin/docker login -u "$DOCKER_USER" -p "$DOCKER_PASS" docker.citr.ous.ca
cd /home/mfenniak/citr.ous.ca/iohint

DOCKER_COMPOSE=/home/mfenniak/bin/docker-compose \
  -f docker-compose.yml \
  -f docker-compose.prod.yml \
  -f docker-compose.admin.yml

$DOCKER_COMPOSE pull
$DOCKER_COMPOSE run migrate
systemctl restart docker.iohint-app.service
