# Standard Imports
import os
import re

# Installed Imports
import docker
from docker.types import TaskTemplate, ContainerSpec, Mount, RestartPolicy, Placement

# Django Imports
from rest_framework.views import APIView, Response, status

# Local Imports
from config import mapping_path, nginx_conf_path, docker_client, base_url, logger
from docker_swarm.utils.nginx_utils import update_nginx_config, restart_nginx
from docker_swarm.utils.scale_up import check_and_scale_up

if mapping_path[-1] == "/":
    mapping_path = mapping_path[:-1]


class ContainerCollection(APIView):
    """
    This 
    """
    def get(self, request):
        """
        List all services in the Docker Swarm.
        """
        try:
            services = docker_client.services.list()
            service_list = []

            for s in services:
                if "code-server" not in s.name:
                    continue

                # logger.error(f"Service: {s.name}")
                # for key, value in s.attrs.items():
                #     logger.error(f"{key}: {value}")

                # Append service details to the list
                service_list.append({
                    "id": s.id,
                    "name": s.name,
                    "status": s.attrs['UpdateStatus']['State'] if 'UpdateStatus' in s.attrs else "active",
                })
            
            return Response({'status': 'success', 'data': service_list})

        except Exception as e:
            response_body = {'error': str(e), "status": "failed"}
            return Response(response_body, status=status.HTTP_400_BAD_REQUEST)


class ContainerResource(APIView):
    def get(self, request, username: str):
        """
        Retrieve details of a service by its name.
        """
        try:
            service_name = f"{username}-code-server"
            service = docker_client.services.get(service_name)
            obj = {
                "service_id": service.id,
                "service_name": service_name,
                "status": service.attrs['UpdateStatus']['State'] if 'UpdateStatus' in service.attrs else "active",
            }
            return Response({'status': 'success', 'data': obj})
        except docker.errors.NotFound:
            response_body = {"error": f"Service '{service_name}' not found.", "status": "failed"}
            return Response(response_body, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            response_body = {'error': str(e), "status": "failed"}
            return Response(response_body, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, username: str):
        """
        Create a new service in Docker Swarm with a unique username as the service name.
        """
        try:
            check_and_scale_up()
            # Ensure the folder for the user exists in mapping_path
            container_mount_path = os.path.join(mapping_path, username)
            user_folder_path = os.path.join("/code-spaces-mapping", username)
            logger.error(f"User folder path: {user_folder_path}")

            if not os.path.exists(user_folder_path):
                logger.error(f"Creating user folder: {user_folder_path}")
                os.makedirs(user_folder_path)

            # Check if a service with the same name already exists
            try:
                existing_service = docker_client.services.get(f"{username}-code-server")
                logger.error(existing_service)
                if existing_service:
                    logger.error("Comming to if")
                    raise ValueError(f"A service with the name '{username}' already exists.")
            except docker.errors.NotFound:
                pass  # No existing service with this name

            # Create the service
            container_spec = ContainerSpec(
                image="taasheeadmin/code-server",
                user="root",
                mounts=[Mount(type="bind", source=container_mount_path, target="/home/coder")],
                tty=True,
                command=["code-server", "--bind-addr", "0.0.0.0:8080", "--auth", "none"]
            )

            # Define task template with placement
            task_template = TaskTemplate(
                container_spec=container_spec,
                restart_policy=RestartPolicy(condition="any"),
                placement=Placement(constraints=["node.role == worker"])
            )

            # Create the service using low-level API
            service = docker_client.api.create_service(
                task_template=task_template,
                name=f"{username}-code-server",
                networks=["code-spaces"]
            )

            # Update Nginx config
            update_nginx_config(username)

            # Restart Nginx to apply changes
            restart_nginx()

            # Return service details
            obj = {
                "message": "Service created successfully!",
                "service_id": service["ID"],
                "service_name": f"{username}-code-server",
                "access_url": f"{base_url}/{username}/?folder=/home/coder",
            }
            return Response({'status': 'success', 'data': obj})

        except Exception as e:
            response_body = {'error': str(e), "status": "failed"}
            return Response(response_body, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, username: str):
        """
        Remove a service by its name.
        Also removes the corresponding location block from nginx.conf and restarts Nginx.
        """
        try:
            service_name = f"{username}-code-server"
            # Remove the service
            service = docker_client.services.get(service_name)
            service.remove()
            
            # Remove location from nginx.conf
            location_block_pattern = rf"\n\s*location /{service_name.replace('-code-server', '')}/ \{{.*?\n\s*\}}"
            
            with open(nginx_conf_path, "r") as file:
                nginx_conf = file.read()

            updated_conf = re.sub(location_block_pattern, "", nginx_conf, flags=re.DOTALL)

            with open(nginx_conf_path, "w") as file:
                file.write(updated_conf)

            # Restart Nginx to apply changes
            restart_nginx()

            response_obj = {"message": f"Service '{service_name}' removed successfully and Nginx updated!", 'status': 'success'}
            return Response(response_obj)
        except docker.errors.NotFound:
            response_body = {"error": f"Service '{service_name}' not found.", "status": "failed"}
            return Response(response_body, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            response_body = {'error': str(e), "status": "failed"}
            return Response(response_body, status=status.HTTP_400_BAD_REQUEST)
