PROD_FILE = docker-compose.yml

COMPOSE_FILE = $(PROD_FILE)

all: run

build:
	docker compose -f  $(COMPOSE_FILE) build --no-cache

run:
	DOCKER_BUILDKIT=1 docker compose -f $(COMPOSE_FILE) up -d --build

down:
	docker compose -f $(COMPOSE_FILE) down

clean:
	docker compose -f $(COMPOSE_FILE) down -v

fclean: clean
	docker system prune -a --volumes

re: fclean all

.PHONY: all build run down clean fclean re dev prod