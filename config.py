import os

import docker
docker_client = docker.from_env()

import logging
logger = logging.getLogger(__name__)

from dotenv import load_dotenv
load_dotenv()

db_name = os.environ.get("POSTGRES_DB")
db_username = os.environ.get("POSTGRES_USER")
db_password = os.environ.get("POSTGRES_PASSWORD")
db_host = os.environ.get("POSTGRES_HOST")
db_port = int(os.environ.get("POSTGRES_PORT", "5432"))

mapping_path = os.getenv("MAPPING_PATH", "~/code-spaces-mapping")
nginx_conf_path = os.getenv("NGINX_CONF_PATH", "/nginx.conf")
base_url = os.getenv("BASE_URL", "http://localhost")

accepted_containers_count = int(os.environ.get("ACCEPTED_CONTAINERS_COUNT", 5))
min_capacity_required = int(os.environ.get("MIN_CAPACITY_REQUIRED", 2))

access_key = os.environ.get("ACCESS_KEY")
secret_access_key = os.environ.get("SECRET_ACCESS_KEY")
region = os.environ.get("REGION")
launch_template_id = os.environ.get("LAUNCH_TEMPLATE_ID", 'lt-0d1c50952a593a1a8')