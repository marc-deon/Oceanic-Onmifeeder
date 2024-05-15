this is a Computer Engineering senior project developed between Fall of 2023 and Spring of 2024.

It is a fish-tank accessory that provides automated feeding, temperature and pH sensor information, and a live video feed from a waterproof camera inside the tank.

https://github.com/marc-deon/Oceanic-Onmifeeder/assets/134232943/1e0852b7-0b9f-4311-8fa0-4f3e5048856a

# Project Structure
There are 3 primary programs here, with their key files being:
1. Embedded system files
   - `4800-embedded.py`
   - `launch-camera.sh`
   - `launch-embedded.sh`
2. Holepunching/authentication server files
   - `4800-server.py`
3. Mobile app written in Godot
   - `VideoTest/`

There are also various files that were used to test certain aspects early on, such as `enet-chat-test.py` and a corrosponding Godot file.

If there is any genuinely useful code to steal from this library, it's either the general structure of `4800-embedded.py` along with `message_queue.py`, or `socket_convenience.py`.

# (Non-exhaustive) Dependancies
- Python 3.10 or higher
- pyenet (from source!): https://github.com/aresch/pyenet
- opencv: https://pypi.org/project/opencv-python/
- imutils: https://pypi.org/project/imutils/
- RPI.GPIO: https://pypi.org/project/RPi.GPIO/
- schedule: https://pypi.org/project/schedule/
