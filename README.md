# CCS Docker

The final, opensource version of CCS

[![Built with Cookiecutter Django](https://img.shields.io/badge/built%20with-Cookiecutter%20Django-ff69b4.svg?logo=cookiecutter)](https://github.com/cookiecutter/cookiecutter-django/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

License: MIT

## About

This is a graph database representation of the Crime Criminal information. It uses Neo4j as the graph database and PostgreSQL as the relational database. The project is dockerized and can be run locally or in a cloud environment. The Getting Started section below will guide you through the process of setting up the project. If you are using this code for your own project, please consider citing my work. In case of any issues in deployment or for customizations, please contact me at `sanjaysingh13@gmail.com`.

## Getting Started

### 1. Clone the Repository

To get started with CCS Docker, first clone the repository:

```bash
git clone https://github.com/sanjaysingh13/ccs_docker_2024.git
cd ccs-docker
```

### 2. Customize Data

Before running the application, you need to customize some data files:

- Replace the `police_stations_districts.csv` file in the `staticfiles/CACHE/` directory with your own data. This file should contain information about police stations and districts relevant to your organization.

- Modify the `home_old.html` file in the `ccs_docker/templates/pages/` directory and other relevant template files to include your organization's specific information and branding.

### 3. Set Up Environment Variables

Create a `.envs` folder in the base directory of the project with two subfolders: `.local` and `.production`. Each subfolder should contain the following files:

- `.django`
- `.postgres`
- `.neo4j`

Here's an example of what these files should contain:

#### .envs/.local/.django

```
DJANGO_READ_DOT_ENV_FILE=True
DJANGO_SETTINGS_MODULE=config.settings.production
DJANGO_SECRET_KEY=your_secret_key_here
DJANGO_ADMIN_URL=admin/
DJANGO_ALLOWED_HOSTS=.example.com

# AWS Settings
DJANGO_AWS_ACCESS_KEY_ID=
DJANGO_AWS_SECRET_ACCESS_KEY=
DJANGO_AWS_STORAGE_BUCKET_NAME=

# Email Settings
DJANGO_EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
DJANGO_EMAIL_HOST=smtp.gmail.com
DJANGO_EMAIL_HOST_USER=
DJANGO_EMAIL_HOST_PASSWORD=
DJANGO_EMAIL_PORT=587
DJANGO_EMAIL_USE_TLS=True

# PostgreSQL
DATABASE_URL=postgres://user:password@localhost:5432/database_name

# Redis
REDIS_URL=redis://redis:6379/0

# Celery
CELERY_BROKER_URL=redis://redis:6379/0

```

Replace the placeholder values with your actual credentials and settings.

#### .envs/.production/.postgres

```
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=ccs_docker
POSTGRES_USER=your_production_postgres_user
POSTGRES_PASSWORD=your_production_postgres_password

```

Replace the placeholder values with your actual credentials and settings. Ensure that you keep your production credentials secure and do not share them publicly.

### 4. Build and Run with Docker

Once you have set up your environment variables and customized your data, you can build and run the application using Docker Compose:

```bash
docker-compose -f local.yml build
docker-compose -f local.yml up
```

This will build the Docker images and start the containers for the CCS Docker application.

### 5. Access the Application

After the containers are up and running, you can access the application by navigating to `http://localhost:8000` in your web browser.

## Settings

Moved to [settings](http://cookiecutter-django.readthedocs.io/en/latest/settings.html).

## Basic Commands

### Setting Up Your Users

- To create a **normal user account**, just go to Sign Up and fill out the form. Once you submit it, you'll see a "Verify Your E-mail Address" page. Go to your console to see a simulated email verification message. Copy the link into your browser. Now the user's email should be verified and ready to go.

- To create a **superuser account**, use this command:

      $ python manage.py createsuperuser

For convenience, you can keep your normal user logged in on Chrome and your superuser logged in on Firefox (or similar), so that you can see how the site behaves for both kinds of users.

### Type checks

Running type checks with mypy:

    $ mypy ccs_docker

### Test coverage

To run the tests, check your test coverage, and generate an HTML coverage report:

    $ coverage run -m pytest
    $ coverage html
    $ open htmlcov/index.html

#### Running tests with pytest

    $ pytest
