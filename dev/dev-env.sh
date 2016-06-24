RABBIT_ID=`docker ps -a -q --filter name=rabbitmq --format="{{.ID}}"`
if [ -n "${RABBIT_ID}" ]; then
  docker stop $RABBIT_ID
  docker rm $RABBIT_ID
fi
docker run -d --name rabbitmq -p 5672:5672 rabbitmq:3.6
