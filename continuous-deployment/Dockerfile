FROM python:3.5-onbuild
RUN curl -fsSL https://get.docker.com/ | sh

# Deploy scripts need to be run as root to allow access to the docker socket, but, we don't want the web user
# flask to be able to access the docker socket.  The idea here is to make the deployment more secure by not
# allowing the public app to run as root, but instead only allow the specific operations that are part of the scripts.
RUN apt-get install sudo && \
  echo "flask ALL = (root) NOPASSWD:SETENV: /usr/src/app/deploy-iohint-app.sh" > /etc/sudoers && \
  chmod +x /usr/src/app/deploy-iohint-app.sh && \
  curl -L https://github.com/docker/compose/releases/download/1.6.2/docker-compose-`uname -s`-`uname -m` > /usr/local/bin/docker-compose && \
  chmod +x /usr/local/bin/docker-compose

RUN groupadd -r flask && useradd -r -g flask flask
USER flask
EXPOSE 6000
CMD [ "gunicorn", "-w", "8", "-b", ":6000", "main:app" ]
