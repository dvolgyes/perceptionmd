#!/usr/bin/env bash
for i in `seq 120`; do
  xdotool click 1
  xdotool key F3
  xdotool key F4
  xdotool key F5
  xdotool key F6
  xdotool key F7
  xdotool key F8
  xdotool key F9
  xdotool key F10
  xdotool key F11
  xdotool key F12
  xdotool key a
  xdotool key b
  xdotool key c
  xdotool key d
  xdotool key e
  xdotool key f
  xdotool key g
  xdotool key h
  xdotool key Enter
  xdotool mousemove 300 300 click 1
  xdotool click --clearmodifiers 5
  sleep 1
  xdotool click --clearmodifiers 4
  sleep 1
done
