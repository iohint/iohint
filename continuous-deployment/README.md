This is a simple Flask application that receives notifications from a Docker registry (eg.
https://docs.docker.com/registry/notifications/) and executes Fabric tasks to perform
deployments.

1) Build this image; `docker build -t ...docker-repo.../iohint-cd:latest .`

2) Push this image to a repo; `docker push ...docker-repo.../iohint-cd:latest`

3) Run this image; pass DOCKER_USER, and DOCKER_PASS environment variables in.  Mount the location of your docker-compose.yml, docker-compose.prod.yml, and docker-compose.admin.yml files at `/iohint`.

```
docker pull ...docker-repo.../iohint-cd:latest
docker create \
  --name iohint-cd \
  -v ...docker-compose.yml-location...:/iohint \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -e "DOCKER_USER=...repo-user..." \
  -e "DOCKER_PASS=...repo-pass..." \
  docker.citr.ous.ca/iohint-cd:latest
docker start iohint-cd
```

4) The image runs a webserver on port 6000 by default.  Host this somewhere.  I recommend using [jwilder/nginx-proxy](https://github.com/jwilder/nginx-proxy).

5) Modify the configuration of your docker registry to push events to this webserver; eg in your config.yml of
docker registry:

```
notifications:
  endpoints:
    - name: deploy
      url: https://...hostname.../event
      headers:
        Authorization: [...secret-token...]
      timeout: 5m
      threshold: 5
      backoff: 1m
```
