#!/bin/bash
TIMESTAMP=$(date +%Y%m%d%H%M%S)
tcpdump -i any -w /home/matthewh/chatty-commander/tcpdump/tcpdump_$TIMESTAMP.pcap & sleep 300
kill $!
