import queue

message_queue = queue.Queue()

def Add(msg:dict):
    message_queue.put(msg)

def Get() -> dict:
    return message_queue.get()

def Empty() -> bool:
    return message_queue.empty()

def clear():
    global message_queue
    message_queue = queue.Queue()
