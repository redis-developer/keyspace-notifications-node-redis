import logging
import os

import redis

LOGGING_LEVEL = os.environ.get("LOGLEVEL", "INFO")
logging.basicConfig(
    format="[%(asctime)s] %(levelname)-8s %(message)s",
    level=LOGGING_LEVEL,
)

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379")
SUB_KEY = "__keyspace@0__:tokens:*"

# pub/sub clients do not allow the execution of non-pubsub commands
# so, we're using a dedicated client for subscribing to keyspace events
# and a dedicated client for non-pubsub commands, needed to handle the scoreboard logic
sub_client = redis.Redis.from_url(REDIS_URL, decode_responses=True).pubsub()
client = redis.Redis.from_url(REDIS_URL, decode_responses=True)


def keyspace_event_handler(event):
    """Handles the keyspace events.

    This is an example of the event format:
    {
        'type': 'pmessage',
        'pattern': '__keyspace@0__:tokens:*',
        'channel': '__keyspace@0__:tokens:luca',
        'data': 'sadd'
    }
    """
    logging.debug(f"Received new event: {event}")
    event_type = event['data']
    channel = event["channel"]
    logging.info(f"event >>> {event_type} on {channel}")
    affected_key = channel.split(":", maxsplit=1)[1]
    how_many = client.scard(affected_key)
    logging.info(f"Set cardinality {affected_key} is {how_many}")

    username = affected_key.split(":")[1]

    if how_many > 0:
        client.zadd("scoreboard", {username: how_many})
    else:
        client.zrem("scoreboard", username)

    scoreboard = client.zrange("scoreboard", 0, -1, desc=True, withscores=True)
    logging.info(f"Scores: {scoreboard}")


def main():
    sub_worker_thread = None
    try:
        logging.debug("Waiting for events...")
        sub_client.psubscribe(**{SUB_KEY: keyspace_event_handler})
        sub_worker_thread = sub_client.run_in_thread(sleep_time=.01)
        sub_worker_thread.join()
    except KeyboardInterrupt:
        pass
    finally:
        # gracefully stops the clients, for example when receives a `KeyboardInterrupt` (e.g. CTRL + c)
        logging.debug("Stopping the application...")
        if sub_worker_thread:
            sub_worker_thread.stop()
        client.close()


if __name__ == "__main__":
    main()
