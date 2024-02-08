#! /usr/bin/env python3

from socket_convenience import utf8get, utf8send, CreateSocket
import enet
from enums import *
import json

# Calls json.dumps with a default
def dumps(o):
    return json.dumps(o, default=lambda x: x.ToDict())


BUFF_SIZE = 65536
HOST_IP = 'highlyderivative.games'
HOST_PORT = 4800
socket_address = (HOST_IP, HOST_PORT)


def enet_main():
    print("Entering enet main")
    userdict = {} # username -> ip ip port port
    hostdict = {} # username -> enet.peer

    enetHost = enet.Host(enet.Address(None, HOST_PORT), peerCount=32)
    while True:
        event = enetHost.service(10000)

        match event.type:
            case enet.EVENT_TYPE_RECEIVE:
                addr = event.peer.address.host
                port = event.peer.address.port
                print("Got message", event.packet.data.decode().split(" "))
                match event.packet.data.decode().split(" "):

                    case ["HOST", local, username, localport]:
                        userdict[username] = local, addr, port, localport
                        hostdict[username] = event.peer
                        event.peer.send(CHANNELS.HOLEPUNCH, enet.Packet(b"HOSTING", enet.PACKET_FLAG_RELIABLE))
                        print("Sent HOSTING")

                    # TODO: Use password
                    case ["CONN", local, username, password, localport]:
                            if username not in userdict:
                                s = "USERNAME_NOT_PRESENT".encode()
                                event.peer.send(0, enet.Packet(s, enet.PACKET_FLAG_RELIABLE))
                                print("Username", username, "not present")
                                continue


                            # TODO: Authenticate here
                            token = server_TryLogin(username, password)
                            if not isinstance(token, Token):
                                s = "AUTHENTICATION FAILED".encode()
                                event.peer.send(0, enet.Packet(s, enet.PACKET_FLAG_RELIABLE))
                                continue

                            # Get the info to send
                            hostlocal, hostaddr, hostport, hostlocalport = userdict[username]

                            # This gets sent back to the original hoster
                            expect = f"EXPECT {addr} {local} {port} {localport}".encode()
                            print(expect)
                            hostdict[username].send(CHANNELS.HOLEPUNCH, enet.Packet(expect, enet.PACKET_FLAG_RELIABLE))

                            # This gets send to the client who just connected
                            connto = f"CONNTO {hostaddr} {hostlocal} {hostport} {hostlocalport}".encode()
                            print(connto)
                            event.peer.send(CHANNELS.HOLEPUNCH, enet.Packet(connto, enet.PACKET_FLAG_RELIABLE))

                            # Remove info from dictionaries
                            #userdict.pop(username)
                            #hostdict.pop(username).disconnect_later()
                            event.peer.disconnect_later()

                    case ["REGISTER", username, password]:
                            print("Register function impl. in progress")
                            token_or_error = server_TryRegister(username, password)
                            if isinstance(token_or_error, Token):
                                print("Sending token")
                                s = dumps({
                                    'error_type': 'OK',
                                    'message': token_or_error
                                }).encode()
                            else:
                                print("Sending error", token_or_error)
                                s = dumps({
                                    'error_type': 'ERROR_REGISTRATION',
                                    'message': token_or_error
                                }).encode()
                            event.peer.send(0, enet.Packet(s, enet.PACKET_FLAG_RELIABLE))
                            print("Sent")

                    case ["LOGIN", username, password]:
                            print("Login function impl. in progress")
                            token_or_error = server_TryLogin(username, password)
                            if isinstance(token_or_error, Token):
                                print("Sending token")
                                s = dumps({
                                    'error_type': 'OK',
                                    'message': token_or_error
                                }).encode()
                            else:
                                print("Sending error", token_or_error)
                                s = dumps({
                                    'error_type': 'ERROR_LOGIN',
                                    'message': token_or_error
                                }).encode()

                            event.peer.send(0, enet.Packet(s, enet.PACKET_FLAG_RELIABLE))

                    case _:
                        s = "Unknown message format".encode()
                        print(s, "from", event.peer.address.host, ":", event.peer.address.port, event.packet.data.decode().split(" "))
                        event.peer.send(CHANNELS.HOLEPUNCH, enet.Packet(s, enet.PACKET_FLAG_RELIABLE))


##########################
## Authentication stuff ##
##########################
# Some functions are marked as internet-facing. Do not confusing the related private functions.
################################################################################################
#
# HOST local username localport
# CONN local username localport
#
# REGISTER username password
# LOGIN username password
#

import datetime
from hashlib import sha256
# Temp dictionary "database"
database = {}
#import sqlite3
#authentication_database = sqlite3.connect("authentication.db")

class AccountError(Exception):
    def ToDict(self):
        return str(self.__class__)

class RegistrationError(AccountError): pass
class UnknownRegistrationError(RegistrationError): pass
class UsernameUnavailableError(RegistrationError): pass

class LoginError(AccountError): pass
class UnknownLoginError(LoginError): pass
class InvalidLoginInfoError(LoginError): pass

# Let's be lazy and assume UTC-5
class SerializableDatetime(datetime.datetime):
    def ToDict(self):
        return {'year':         self.year,
                'month':        self.month,
                'day':          self.day,
                'hour':         self.hour,
                'second':       self.second,
                'microsecond':  self.microsecond}

# TODO: Token should have an invalid date etc etc
class Token():
    def __init__(self, hash:str = None, invalid_after:SerializableDatetime = None):
        now = SerializableDatetime.now()
        self.hash = hash if hash else _server_Hash(str(now))
        inamonth = now + datetime.timedelta(days=30)
        self.invalid_after = invalid_after if invalid_after else inamonth

    def ToDict(self):
        return {'hash': self.hash, 'invalid_after': self.invalid_after}


# Retrieve a value from the database.
def _server_DatabaseRead(key) -> str:
    return database[key]


# Write a value to the database.
def _server_DatabaseWrite(key, val) -> None:
    database[key] = val
    _server_DatabaseSave()


# TODO: Don't use json
# Save database to file
def _server_DatabaseSave() -> None:
    with open("auth_database.json", 'w') as f:
        f.write(dumps(database))


# Load database from file
def _server_DatabaseLoad() -> None:
    with open("auth_database.json", 'r') as f:
        global database
        database = json.loads(f.read())


# Check if a key exists in the database.
def _server_DatabaseExist(key) -> bool:
    return key in database


# Check if a username already exists in the database
def _server_IsUsernameAvailable(username) -> bool:
    if username in database:
        return False
    return True


# Internet-facing function: Try to register using a given username and password and return either a session Token or RegistrationError
def server_TryRegister(username, password) -> Token | RegistrationError:
    if _server_IsUsernameAvailable(username):
        return _server_Register(username, password)
    else:
        return UsernameUnavailableError()


# string -> string sha256 hash
def _server_Hash(potato:str) -> str:
     return sha256(potato.encode()).hexdigest()


# Generate a session token
def _server_GenerateToken() -> str:
    # TODO: Implement
    return Token()


# Private function: Username already checked for (non)existence, register the username+hash in database and return session Token or Error
def _server_Register(username, password) -> Token | RegistrationError:
    hash = _server_Hash(password)
    _server_DatabaseWrite(username, hash)
    print("Registered successfully", username, password, hash)
    return  _server_GenerateToken()


# Internet-facing function: Attempt to log in with a username and password and return session Token or Error
def server_TryLogin(username, password) -> Token | LoginError:
    if not _server_DatabaseExist(username):
        return InvalidLoginInfoError()

    computed_hash = _server_Hash(password)
    stored_hash = _server_DatabaseRead(username)

    if computed_hash == stored_hash:
        return _server_GenerateToken()
    else:
        return InvalidLoginInfoError()


if __name__ == "__main__":
    _server_DatabaseLoad()
    enet_main()
