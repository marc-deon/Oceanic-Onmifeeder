#rpicam-vid --framerate 20 --width 640 --height 480 -t 0 --inline -o udp://127.0.0.1:6969 &

# Several errors can be fixed by doing `fuser /dev/video0` and closing the shown processes

# use -n to supress log messages
sudo modprobe w1-gpio
sudo modprobe w1-therm
source bin/activate
rpicam-vid --framerate 10 --width 320 --height 240 -t 0 --inline -o 'udp://127.0.0.1:6969?overrun_nonfatal=1&fifo_size=10000' &
./4800-embedded.py
