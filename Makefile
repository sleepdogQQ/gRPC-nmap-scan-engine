.PHONY: docker_init , clear_whole_progrme, docekr_image_clean, venv_build, output_venv, build_proto, generate_ca_crt, generate_server_crt

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


# === SSL Scripts ===
CA_KEY = base_grpc/SSL/ca.key
CA_CRT = base_grpc/SSL/ca.crt
SERVER_KEY_PATH = base_grpc/SSL/server.key
SERVER_CSR_PATH = base_grpc/SSL/server.csr
SERVER_CRT_PATH = base_grpc/SSL/server.crt

generate_ca_crt:
# 生成 .key 私鑰文件
	@openssl genrsa -out $(CA_KEY) 2048
# 自簽名生成 .crt 證書文件
	@openssl req -new -x509 -days 3650 \
    -key $(CA_KEY) -out $(CA_CRT) \
    -subj "/C=TW/ST=Taiwan/L=Taipei/O=SYSTEX INC./OU=B800/CN=B85B_gRPC_CA"

generate_server_crt:
# 生成 .key 私鑰文件
	@openssl genrsa -out $(SERVER_KEY_PATH) 2048
# 生成 .csr 證書簽名請求文件
	@openssl req -new -key $(SERVER_KEY_PATH) -config ssl.conf -out $(SERVER_CSR_PATH)
# 給 CA 簽名生成 .crt 證書文件
	@openssl x509 -req -CAcreateserial -days 3650 -sha256 \
    -CA $(CA_CRT) -CAkey $(CA_KEY) \
    -in $(SERVER_CSR_PATH) \
    -out $(SERVER_CRT_PATH)
# 刪除 .csr 文件
	@ rm $(SERVER_CSR_PATH)