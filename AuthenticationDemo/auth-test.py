#!/usr/bin/env python

##################
## Server stuff ##
##################
# Some functions are marked as internet-facing. Do not confusing the related private functions.
################################################################################################

from hashlib import sha256
# TODO: Which single-file database format does Pycharm's django project use? That should work fine here.
database = {}

class AccountError(Exception): pass

class RegistrationError(AccountError): pass
class UnknownRegistrationError(RegistrationError): pass
class UsernameUnavailableError(RegistrationError): pass

class LoginError(AccountError): pass
class UnknownLoginError(LoginError): pass
class InvalidLoginInfoError(LoginError): pass

# TODO: Token should have an invalid date etc etc
class Token(str): pass


# Retrieve a value from the database.
def _server_DatabaseRead(key) -> str:
    return database[key]


# Write a value to the database.
def _server_DatabaseWrite(key, val) -> None:
    database[key] = val


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
def _server_Hash(potato) -> str:
     return sha256(potato.encode()).hexdigest()


# Generate a session token
def _server_GenerateToken() -> str:
    # TODO: Implement
    return Token("foobar")


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


##################
## Client stuff ##
##################

# Ask for username and password
def client_UserPass() -> tuple:
    while not (username := input("Username? ")):
        pass
    while not (password := input("Password? ")):
        pass
    return username, password

def client_Register(username, password):
    print(f"Your desired username and password are [{username}] [{password}]")

    token = server_TryRegister(username, password)
    print("You have registered. Your token is", token, "\n")


def client_Login(username, password):
    print(f"Logging in as [{username}]...")
    token = server_TryLogin(username, password)
    
    if isinstance(token, LoginError):
        print("Error logging in\n")
    else:
        print("Welcome", username, token, "\n")


def client_Quit():
    print("Goodbye")
    exit(0)


def main():
    options = [
        "Register new account",
        "Log in to account",
        "Quit"
    ]

    while True:
        print("What would you like to do?")
        for i, o in enumerate(options):
            print(f"{i+1}) {o}")
        
        inp = int(input("> "))
        match inp:
            case 1:
                username, password = client_UserPass()
                client_Register(username, password)
            case 2:
                username, password = client_UserPass()
                client_Login(username, password)
            case 3:
                client_Quit()

main()