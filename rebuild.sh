#!/bin/bash
app="grahams/snfc-posting-tool:latest"
docker rmi ${app}
docker buildx build --tag ${app} .
