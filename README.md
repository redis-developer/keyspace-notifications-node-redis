# Redis Keyspace Notifications with Node Redis

TODO background on this project and what we'll do...

https://redis.io/docs/manual/keyspace-notifications/

## Get the Code

TODO cloning repo and pre-requisites...

## Configuring and Starting Redis

For performance reasons, keyspace notifications are off by default.  If you're using the supplied Docker Compose file, this will start a Redis Stack container and pass it [extra configuration settings](https://redis.io/docs/stack/get-started/install/docker/#environment-variables) that enable a subset of keyspace notifications that we need for our application.  If you go this route, there's nothing to do here - just start Redis Stack:

```bash
$ docker-compose up -d
```

When you want to stop the container:

```bash
$ docker-compose down
```

Alternatively, you could also turn on keyspace notifications by starting Redis then using the [`CONFIG SET`](https://redis.io/commands/config-set/) command in `redis-cli` or using the command line built into RedisInsight (if using Docker Compose, RedisInsight is available at `http://localhost:8001`).  Let's enable keyspace events (`K`) for both Redis Set commands (`s`) and generic commands (`g` - we will want this to catch `DEL` commands):

```
127.0.0.1:6379> config set notify-keyspace-events Ksg
```

If you're using a locally installed Redis with a `redis.conf` file, enable the keyspace notifications we want to use by changing the following line in that file:

```
notify-keyspace-events ""
```

to read:

```
notify-keyspace-events "Ksg"
```

then restart your Redis server.

Whichever method you use, verify that your configuration changes are active using `redis-cli` or the command line in RedisInsight:

```bash
$ redis-cli
127.0.0.1:6379> config get notify-keyspace-events
1) "notify-keyspace-events"
2) "gsK"
```

See the [Keyspace Notifications configuration docs](https://redis.io/docs/manual/keyspace-notifications/#configuration) for more information on configuring events.

## Application Setup

TODO

## Running the Application

TODO

## Generating Events

TODO