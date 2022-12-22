.PHONY: docker_init , clear_whole_progrme, docekr_image_clean, venv_build, output_venv, build_proto

Dockerfile_Name = Dockerfile
SETTING_FILE = docker-deploy.yml

all: docekr_image_clean remove_all_image docker_init

docker_build:
	@docker build -f $(Dockerfile_Name) .
docker_init: docker_build
	@docker-compose -f $(SETTING_FILE) up -d

docker_clean:
	@docker ps -aq | xargs docker stop | xargs docker rm
docker_volume_clean:
	@docker volume prune
docekr_image_clean:docker_clean docker_volume_clean
	@docker image prune

remove_all_image:
	@docker rmi -f $$(docker images -aq)

remove_poetry_venv:
	@rm -f pyproject.toml
	@rm -f poetry.lock
	@rm -rf .venv

venv_build: remove_poetry_venv
	@poetry init 
	@poetry add $$(cat requirements.txt)
	@poetry shell

output_venv:
	@poetry export -o requirements_test.txt --without-hashes

build_proto:
	@python3 -m grpc_tools.protoc -I ./ --pyi_out=. --python_out=. --grpc_python_out=. ./scan.proto