#rpicam-vid --framerate 20 --width 640 --height 480 -t 0 --inline -o udp://127.0.0.1:6969 &

# Several errors can be fixed by doing `fuser /dev/video0` and closing the shown processes

# use -n to supress log messages
rpicam-vid -t 0 --inline -o udp://127.0.0.1:6969 &
./4800-embedded.py
