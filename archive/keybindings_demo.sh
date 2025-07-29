#!/bin/bash
sleep 10

echo "Demonstrating Alt+Tab"
xdotool keydown Alt key Tab keyup Alt
sleep 5

echo "Demonstrating Alt+Shift+Tab"
xdotool keydown Alt keydown Shift key Tab keyup Shift keyup Alt
sleep 5

echo "Demonstrating Super+1"
xdotool keydown Super key 1 keyup Super
sleep 5

echo "Demonstrating Ctrl+Alt+Left"
xdotool keydown Ctrl keydown Alt key Left keyup Alt keyup Ctrl
sleep 5

echo "Demonstrating Ctrl+Alt+Right"
xdotool keydown Ctrl keydown Alt key Right keyup Alt keyup Ctrl
sleep 5

echo "Demonstrating Fullscreen (F11)"
xdotool key F11
sleep 5

echo "Clicking at (900, 400)"
xdotool mousemove 900 400 click 1

