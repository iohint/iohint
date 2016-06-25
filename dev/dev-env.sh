RABBIT_ID=`docker ps -a -q --filter name=rabbitmq --format="{{.ID}}"`
if [ -n "${RABBIT_ID}" ]; then
  docker stop $RABBIT_ID
  docker rm $RABBIT_ID
fi
docker run -d --name rabbitmq -p 5672:5672 rabbitmq:3.6

PGSQL_ID=`docker ps -a -q --filter name=pgsql --format="{{.ID}}"`
if [ -n "${PGSQL_ID}" ]; then
  docker stop $PGSQL_ID
  docker rm $PGSQL_ID
fi
docker run -d --name pgsql -e POSTGRES_PASSWORD=password -p 15432:5432 postgres:9.6

export SECRET_KEY="rYj8SB6sbrV3nzu87seJhPfkehurv5nd4nC5tEjF"
export APP_DEBUG=1
export DATABASE_URL="postgres://postgres:password@localhost:15432/postgres"
