all: build

.PHONY: build
build:
	DOCKER_BUILDKIT=1 docker build -t boatpilot .

debug:
	docker-compose run --rm --service-ports boatpilot
