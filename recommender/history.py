from dataclasses import dataclass, field
from threading import Thread
from collections import defaultdict
import pika

import sys
import os
import json

def check_env_var(var, error_message):
    try:
        return os.environ[var]
    except KeyError:
        print(error_message)
        sys.exit(-1)

MESSAGE_QUEUE_URL = check_env_var("MESSAGE_QUEUE_URL", "MESSAGE_QUEUE_URL environment variable missing!")

@dataclass(order=True)
class HistoryRecord:
    movieID: str
    userID: str = field(compare=False)
    seen: bool = field(compare=False)

queueName = "history"
userHistories = defaultdict(list)

def isString(s):
    return type(s) == type("")

def getHistoryForUser(userID):
    print(f"[DEBUG] {userID} => {userHistories}")
    return userHistories[userID] # defaultdict ensures no KeyError

def callback(ch, method, properties, body):
    print(f"[DEBUG] Received {body}")

    messageBody = json.loads(body)
    if ( isString(messageBody["userID"]) and isString(messageBody["userID"]) ):
        messageBody["seen"] = False

        # https://stackoverflow.com/questions/72013377/how-to-parse-a-json-object-into-a-python-dataclass-without-third-party-library
        record = HistoryRecord(**messageBody) # ** "unwraps" the dict object into the dataclass

        print(f"[DEBUG] {record}")
        userHistories[messageBody["userID"]].append(record)
        # expected schema: { userID: string; movieID: string; }
    else:
        pass # ignore malformed records, but ack them anyway

    ch.basic_ack(delivery_tag=method.delivery_tag)

def createConnection():
    connection = pika.BlockingConnection(pika.URLParameters(MESSAGE_QUEUE_URL))
    channel = connection.channel()
    channel.queue_declare(queueName, durable=True)
    channel.basic_consume(queue=queueName, on_message_callback=callback)
    return channel

def DEBUG_getHistories():
    return userHistories

def history_init():
    channel = createConnection()
    print('[DEBUG] Waiting for messages')
    thread = Thread(target=channel.start_consuming)
    thread.start()