# Redis Keyspace Notifications with Node Redis

TODO background on this project and what we'll do...

TODO embed a GIF of 2 Terminals showing this working...

https://redis.io/docs/manual/keyspace-notifications/

## Prerequisites

To try out this project yourself, you'll need:

* [Redis](https://redis.io) (install locally or use the supplied Docker Compose file).
* [Docker Desktop](https://www.docker.com/products/docker-desktop/) (if using the Docker Compose file).
* [git](https://git-scm.com/download) command line tools.
* [Node.js](https://nodejs.org/) version 14.8 or higher.

## Get the Code

To get the code, clone the repo to your machine:

```bash
$ git clone https://github.com/redis-developer/keyspace-notifications-node-redis.git
$ cd keyspace-notifications-node-redis
```

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

To setup the application, first install the dependencies:

```bash
$ npm install
```

The application expects to find Redis at `localhost` on port `6379` with no password.  These are the default values when installing Redis.

If your Redis server is located elsewhere and/or requires a password, set the value of the `REDIS_URL` environment variable to a valid [Redis connection URL](https://github.com/redis/node-redis#usage) before starting the application.  For example:

```bash
$ export REDIS_URL=redis://simon:sssssh@redis.mydomain.com:6390
```

## Running the Application

Start the application as follows:

```bash
$ npm run dev
```

This uses [nodemon](https://www.npmjs.com/package/nodemon) which will restart the application for you automatically every time you make a code change.

## Generating Events

You won't see any output from the application until you make changes in Redis that generate the sorts of keyspace events that you enabled earlier, and which affect the portion of the keyspace that the application is listening for.  We'll look at how that works later in this document, but for now let's try changing data in Redis in ways that generate appropriate events and watch the application react to them and update our high score table...

First, with the application running, connect to Redis using `redis-cli` or Redis Insight.  

Let's assume that a few users playing our game have found some of the tokens, and we want to represent that by adding each token to a Redis Set whose key name has the user name in it:

```bash
$ redis-cli
127.0.0.1:6379> sadd tokens:simon a b c
(integer) 3
127.0.0.1:6379> sadd tokens:suze a d e f
(integer) 4
127.0.0.1:6379> sadd tokens:steve a b c f g
(integer) 5
```

Take a look at the terminal where the Node.js application is running.  You should see that each time we ran the [`SADD` command](https://redis.io/commands/sadd/), an event was generated and the application created and updated a high score table (stored as a [Redis Sorted Set](https://redis.io/docs/manual/data-types/#sorted-sets) in a key named `scoreboard`):

```
event >>> sadd on __keyspace@0__:tokens:simon
Set cardinality tokens:simon is 3
Scores:
[ { value: 'simon', score: 3 } ]
event >>> sadd on __keyspace@0__:tokens:suze
Set cardinality tokens:suze is 4
Scores:
[ { value: 'suze', score: 4 }, { value: 'simon', score: 3 } ]
event >>> sadd on __keyspace@0__:tokens:steve
Set cardinality tokens:steve is 5
Scores:
[
  { value: 'steve', score: 5 },
  { value: 'suze', score: 4 },
  { value: 'simon', score: 3 }
]
```

Let's remove a token from one user, and delete another entirely:

```bash
127.0.0.1:6379> srem tokens:steve c
(integer) 1
127.0.0.1:6379> del tokens:simon
(integer) 1
```

The output from the Node.js application looks like this:

```
event >>> srem on __keyspace@0__:tokens:steve
Set cardinality tokens:steve is 4
Scores:
[
  { value: 'suze', score: 4 },
  { value: 'steve', score: 4 },
  { value: 'simon', score: 3 }
]
event >>> del on __keyspace@0__:tokens:simon
Set cardinality tokens:simon is 0
Scores:
[ { value: 'suze', score: 4 }, { value: 'steve', score: 4 } ]
```

## How does it Work?

TODO
