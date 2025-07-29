#!/bin/bash
# Launch applications
gnome-terminal -- bash -c "nvtop; exec bash" &
gnome-terminal -- bash -c "htop; exec bash" &
gnome-terminal -- bash -c "pavucontrol; exec bash" &
gnome-terminal -- bash -c "alsamixer; exec bash" &
epiphany-browser &

# Start tcpdump to capture network traffic for 5 minutes
TIMESTAMP=$(date +%Y%m%d%H%M%S)
echo "Running tcpdump to capture network traffic for troubleshooting..."
tcpdump -i any -w /home/matthewh/chatty-commander/tcpdump/tcpdump_$TIMESTAMP.pcap & sleep 300
kill $!
echo "Tcpdump capture completed. File saved as /home/matthewh/chatty-commander/tcpdump/tcpdump_$TIMESTAMP.pcap"

# Run keybindings demo script
/home/matthewh/chatty-commander/keybindings_demo.sh

