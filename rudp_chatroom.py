from socket_convenience import *
from dataclasses import dataclass
from datetime import datetime
import json
import base64
import time
import curses
import threading
import os
from rudp import RudpPort, RudpTimeout

@dataclass
class Message:
    system:bool
    user:str
    time:datetime
    text:str

    def FromString(msg:str) -> 'Message':
        t = type(msg)
        msg = base64.b64decode(msg).decode('utf8')
        msg = json.loads(msg)
        return Message(msg["system"],msg["user"], msg["time"], msg["text"])


class Chatroom:

    def __init__(self, send_socket:RudpPort, recieve_socket:RudpPort, username=""):
        self.send_socket = send_socket
        self.recieve_socket = recieve_socket

        self.localUser = username
        while self.localUser == "":
            self.localUser = input("Enter your name: ").strip()

        self.log = [Message(False, "System", time.gmtime(), f"Welcome to the chat, {self.localUser}!")]


    def Listen(self) -> None:
        while True:
            try:
                # Strip leading b' and trailing '
                # Shenanigans from double encoding as bytes
                message = Message.FromString(self.recieve_socket.Receive().data)
                

                if message.system:
                    if message.text == "DISCONNECT":
                        # exit(0)
                        os._exit(0)
                        
                self.log.append(message)

            except RudpTimeout:
                pass


    def Send(self, message:str, system:bool=False) -> None:
        # Create a local copy of the message
        self.log.append(Message(False, self.localUser, time.gmtime(), message))
        # Create a json copy of the message, encoded in utf8, base64
        msg = json.dumps({"system":system, "user": self.localUser, "text":message, "time": time.gmtime()})
        msg = base64.b64encode(msg.encode())
        # Send it
        self.send_socket.Send(msg)


    def SendDisconnect(self) -> None:
        self.Send("DISCONNECT", system=True)


    def DrawLogWindow(self) -> None:
        # Clear any rightward junk that wouldn't be overwritten otherwise
        self.logWindow.clear()
        self.logWindow.move(1,1)
        # Only show past 10 messages
        for m in self.log[-10:]:
            # Show black on white for other user's messages,
            # white on black for ours
            rev = curses.A_REVERSE if m.user != self.localUser else 0
            self.logWindow.addstr(f"{m.user}: {m.text}\n ", rev)
        self.logWindow.border()
        self.logWindow.refresh()

    def DrawMessageWindow(self, currentMessage) -> None:
        self.messageWindow.clear()
        self.messageWindow.addstr(1,1, currentMessage)
        self.messageWindow.border()
        self.messageWindow.refresh()


    def main(self, screen) -> None:
        currentMessage = ""
        self.screen = screen

        y, x = screen.getmaxyx()
        self.logWindow  = screen.subwin(y-3, x, 0, 0)
        self.messageWindow  = screen.subwin(3, x, y-3, 0)

        curses.noecho()
        curses.halfdelay(1)

        t = threading.Thread(target = self.Listen)
        t.start()

        while True:
            try:
                k = screen.getkey()

                match k:
                    case os.linesep:
                        self.Send(currentMessage)
                        currentMessage = ""

                    case "KEY_BACKSPACE":
                        currentMessage = currentMessage [:-1]

                    case _:
                        currentMessage += k

            except curses.error:
                pass
            except (KeyboardInterrupt):
                os.system('stty sane')
                self.SendDisconnect()
                exit()

            self.DrawLogWindow()
            self.DrawMessageWindow(currentMessage)
            curses.doupdate()
