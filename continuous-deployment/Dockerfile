FROM python:3.5-onbuild
RUN curl -fsSL https://get.docker.com/ | sh

# Deploy scripts need to be run as root to allow access to the docker socket, but, we don't want the web user
# flask to be able to access the docker socket.  The idea here is to make the deployment more secure by not
# allowing the public app to run as root, but instead only allow the specific operations that are part of the scripts.
RUN apt-get install sudo && \
  echo "flask ALL = (root) NOPASSWD:SETENV: /usr/src/app/deploy-iohint-celery-beat.sh, (root) NOPASSWD:SETENV: /usr/src/app/deploy-iohint-celery-worker.sh" > /etc/sudoers && \
  chmod +x /usr/src/app/deploy-iohint-celery-beat.sh

RUN groupadd -r flask && useradd -r -g flask flask
USER flask
EXPOSE 6000
CMD [ "python", "./main.py" ]
