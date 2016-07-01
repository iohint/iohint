Dockerfile-postgres
-------------------

This is a Docker image that builds on postgres:9.6 to install [wal-e](https://github.com/wal-e/wal-e), a continuous
archiving tool for PostgreSQL.  To use this image with wal-e, and specifically with AWS S3 backups:

  1) Build the image, push to a repo

  2) Replace the base image in docker-compose.yml with a reference to this image.

  3) Create an AWS IAM user for the backups.  The user should have a policy that allows s3:GetObject and s3:PutObject
     to `arn:aws:s3:::...yourbucket.../*`, and s3:ListBucket to `arn:aws:s3:::...yourbucket...`.

  4) Update docker-compose.prod.yml, populating the environment variables on iohint-pgsql with your S3 information.

  5) Update your postgresql.conf settings, then restart your PostgreSQL container:

      wal_level = archive
      archive_mode = on
      archive_command = 'wal-e wal-push %p'
      archive_timeout = 60

  6) Start a base backup to restore from in the future.  You should automate doing this on a regular schedule.

      docker exec -it iohint_iohint-pgsql wal-e backup-push /var/lib/postgresql/data
