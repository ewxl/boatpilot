all: build

.PHONY: build
build:
	DOCKER_BUILDKIT=1 docker build -t elof/boatpilot .

debug:
	docker-compose run --rm --service-ports boatpilot

dualshock:
	docker run --rm -it -v $(PWD)/app:/usr/src/app --device /dev/input:/dev/input boatpilot python3 inputs.py
