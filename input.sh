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
  xdotool type a
  xdotool type b
  xdotool type c
  xdotool type d
  xdotool type e
  xdotool type f
  xdotool type g
  xdotool type h
  xdotool type Enter
  xdotool mousemove 300 300 click 1
  xdotool click --clearmodifiers 5
  sleep 0.2
  xdotool click --clearmodifiers 4
  sleep 0.2

  xdotool mousedown 1
  sleep 0.2
  xdotool mousemove_relative  50 0
  sleep 0.2
  xdotool mousemove_relative  -50 0
  sleep 0.2
  xdotool mouseup 1
  sleep 0.2
  xdotool mousedown 1
  xdotool mousemove_relative  0 50
  sleep 0.2
  xdotool mousemove_relative  0 -50
  sleep 0.2
  xdotool mouseup 1

  xdotool mousedown 2
  sleep 0.2
  xdotool mousemove_relative  50 0
  sleep 0.2
  xdotool mousemove_relative  -50 0
  sleep 0.2
  xdotool mouseup 2
  sleep 0.2
  xdotool mousedown 2
  xdotool mousemove_relative  0 50
  sleep 0.2
  xdotool mousemove_relative  0 -50
  sleep 0.2
  xdotool mouseup 2

done