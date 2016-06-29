iohint environment
------------------

iohint leverages Docker for consistent packaged application deployments.

Required dependencies: a RabbitMQ server, and a PostgreSQL server.  Both of
these can be managed by the docker-compose file included in this project.

Deployment
==========

Copy docker-compose.prod-template.yml into docker-compose.prod.yml.  You can
then customize:

  1) Populate my-secret-key with a random secret key appropriate for a Django
  application.

  2) Update the volumes for the RabbitMQ and PostgreSQL server to point to
  appropriate persistent data storage.
  
  3) ```docker-compose -f docker-compose.yml -f docker-compose.prod.yml up```

Note that docker.citr.ous.ca is a private Docker server, but, the images
pushed there are built out of this repository from the circle.yml file, so
they could easily be reproduced and hosted in a public location.  (In fact...
that sounds like a great idea... why am I pushing Open Source software into a
private repo?  Well, I had the private repo available... and didn't much think
about it.)

Administration
==============

docker-compose.admin.yml has a few utility commands present for access to the
system.

- docker-compose -f docker-compose.yml -f docker-compose.admin.yml run migrate

  Runs DB migration scripts defined in the application to create or update the
  database schema.

- docker-compose -f docker-compose.yml -f docker-compose.admin.yml run django-shell

  Starts a Python interactive shell in the Django application.

- docker-compose -f docker-compose.yml -f docker-compose.admin.yml run psql

  Starts a psql client application connected to the iohint database.
