#!/bin/sh

cd pox
./pox.py openflow.of_01 forwarding.l2_learning firewall --path_archivo=../config.json
# ./pox.py log.level --DEBUG openflow.of_01 forwarding.l2_learning firewall --path_archivo=../config.json
cd ..
