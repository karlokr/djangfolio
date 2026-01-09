.PHONY: build run stop clean restart logs shell

# Image name and tag
IMAGE_NAME = portfolio-site
IMAGE_TAG = latest
IMAGE = $(IMAGE_NAME):$(IMAGE_TAG)

# Build the Docker image
build:
	docker build -t $(IMAGE) .

# Build without cache
build-no-cache:
	docker build --no-cache -t $(IMAGE) .

