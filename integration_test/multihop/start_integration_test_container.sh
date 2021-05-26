#!/bin/bash
docker build . -f Dockerfile_multihop -t multihop-peer
docker run --network host --env-file integration_test/multihop/env_node_2 --name node-2 -d multihop-peer:latest
sleep 5
docker run --network host --env-file integration_test/multihop/env_node_1 --name node-1 -d multihop-peer:latest
sleep 2
docker run --network host --env-file integration_test/multihop/env_node_3 --name node-3 -d multihop-peer:latest