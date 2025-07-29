#!/bin/bash
sleep 10

# Basic file and process checks
echo "Verifying the existence and size of the files:"
ls -l /home/matthewh/chatty-commander/keybindings_demo.sh /home/matthewh/chatty-commander/startup_apps.sh /home/matthewh/chatty-commander/.config/autostart/startup_apps.desktop /home/matthewh/chatty-commander/scripts_content.txt

echo -e "
Contents of keybindings_demo.sh:"
cat /home/matthewh/chatty-commander/keybindings_demo.sh

echo -e "
Contents of startup_apps.sh:"
cat /home/matthewh/chatty-commander/startup_apps.sh

echo -e "
Contents of autostart entry (startup_apps.desktop):"
cat /home/matthewh/chatty-commander/.config/autostart/startup_apps.desktop

echo -e "
Contents of scripts_content.txt:"
cat /home/matthewh/chatty-commander/scripts_content.txt

echo -e "
Checking executable permissions:"
ls -l /home/matthewh/chatty-commander/keybindings_demo.sh /home/matthewh/chatty-commander/startup_apps.sh

echo -e "
Checking running processes:"
ps aux | grep nvtop
ps aux | grep htop
ps aux | grep pavucontrol
ps aux | grep alsamixer
ps aux | grep epiphany-browser

# Audio troubleshooting steps
echo -e "
### Audio Troubleshooting ###"

echo -e "
1. Listing ALSA settings:"
aplay -l
arecord -l

echo -e "
2. ALSA Mixer settings:"
amixer scontrols
amixer scontents

echo -e "
3. Checking Pulseaudio status:"
pulseaudio --check
pulseaudio --version

echo -e "
4. List Pulseaudio sources and sinks:"
pactl list short sources
pactl list short sinks

echo -e "
5. Pulseaudio default settings:"
pactl info

echo -e "
Audio troubleshooting completed."

