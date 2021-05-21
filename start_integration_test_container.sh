#!/bin/bash
docker build . -t multihop-peer
docker run --network host --env-file env_node_1 --name node-1 -d multihop-peer:latest
docker run --network host --env-file env_node_2 --name node-2 -d multihop-peer:latest