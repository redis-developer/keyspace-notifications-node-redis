# Redis Keyspace Notifications with Node Redis

TODO background on this project and what we'll do...

Here's what it looks like when running... in the left hand terminal I'm manipulating the contents of Redis Sets - one for each player that's collecting tokens in the game.  On the right, the Node.js application is reacting to the keyspace events that are raised, and is updating the high score table that we keep as a Redis Sorted Set.

![demo](keyspace_events_demo.gif)

TODO

https://redis.io/docs/manual/keyspace-notifications/

## Prerequisites

To try out this project yourself, you'll need:

* [Redis](https://redis.io) (install locally or use the supplied Docker Compose file).
* [Docker Desktop](https://www.docker.com/products/docker-desktop/) (if using the Docker Compose file).
* [git](https://git-scm.com/download) command line tools.
* [Node.js](https://nodejs.org/) version 14.8 or higher.

If you're not familiar with how pub/sub works in Redis, you may want to read the [guide on redis.io](https://redis.io/docs/manual/pubsub/).

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

All of the code for this application is contained in a single file: `index.js`.

The keyspace notification events are generated by Redis itself, so there's no code required to create these.  Instead our application needs to listen for them and take appropriate action.

The [`PSUBSCRIBE`](https://redis.io/commands/psubscribe/) command is one of the ways that we can listen for pub/sub events.  The `P` in `PSUBSCRIBE` stands for "Pattern".  Redis publishes pub/sub events to named channels.  This command listens for events on pub/sub channels that match a glob style pattern.

The `PSUBSCRIBE` command is also a blocking command.  This means that the Redis client connection that we use it from becomes tied up for this purpose only and can't be used to send other commands to Redis.  As we want to issue other Redis commands while processing a keyspace event, we'll need a second connection to Redis.  Node-Redis facilitates this like so:

```javascript
import { createClient } from 'redis';

const REDIS_URL = process.env.REDIS_URL || 'redis://localhost:6379';

const client = createClient({
  url: REDIS_URL
});

// First connection to Redis.
await client.connect();

// Let's duplicate that and have a second connection that we'll use for PSUBSCRIBE
const subClient = client.duplicate();
await subClient.connect();
```

Now we've got two connections, let's wait for keyspace pub/sub events on channels named `__keyspace@0__:tokens:*` (keyspace events on keys where the key name begins `tokens:*`):

```javascript
await subClient.pSubscribe('__keyspace@0__:tokens:*', async (message, channel) => {
  console.log(`event >>> ${message} on ${channel}`);
  // Do something...
});
```

We're using `subClient` as the blocked/listening connection to Redis here... so if we want to issue further Redis commands in the callback function, we'll have to do that with `client`, our other connection to Redis.

We know from our keyspace notifications configuration that each event we get notified about involves some sort of change in the keyspace for keys beginning with `tokens:`.  We can assume (because we're the ones creating the application) that all keys beginning `tokens:` are Redis Sets, representing the tokens that a given user has collected in our game.  We can also assume that the key names are of the form `tokens:<username>` e.g. `tokens:simon`.

With those assumptions made, we can now start working on processing the notification event.

The value of `channel` will look something like this:

```
__keyspace@0__:tokens:simon
```

Where `tokens:simon` is the Redis key that was affected, and `simon` is the username of the player in our game.  Let's parse these values out of `channel`:

```javascript
  const affectedKey = channel.substring('__keyspace@0__:'.length);
  const userName = affectedKey.split(':')[1];
```

Now we have the user's username and key, we want to:

* See how many tokens they currently have in their tokens set.
* Update the leaderboard, creating it if necessary.
* Print out the current leaderboard.

Let's look at each in turn...

We receive keyspace notification events whenever the set is modified... we know that our application's going to perform three types of operation on a user's token set:

* Add a new token (adding the first token with [`SADD`](https://redis.io/commands/sadd/) creates the set for us).
* Remove a token (removing the last token with [`SREM`](https://redis.io/commands/srem/) also deletes the set for us).
* Delete the whole set because they left the game (achieved with the [`DEL`](https://redis.io/commands/del/) command).

The Redis command to get the cardinality or number of members in a set is [`SCARD`](https://redis.io/commands/scard/).  We can actually use this one command to cover all three of the above scenarios, without needing to know which scenario triggered the keyspace event.  We can do this because `SCARD` returns the cardinality of the set at a given key, or 0 if the key doesn't exist.  This means we don't need a separate check for the "user left the game" scenario.

With that said, let's see how many tokens are in the affected set:

```javascript
const howMany = await client.sCard(affectedKey);
```

`howMany` is now going to be 0 (user left the game) or > 0 (user is still in the game and just gained or lost a token).  With this information, we can now update the high score table, or create it if it doesn't alredy exist.

The high score table uses a Redis [Sorted Set](https://redis.io/docs/manual/data-types/#sorted-sets), which associates a value (we'll use the username here) with a score (the number of tokens) and keeps the members sorted by score.

We only need to use one of two Sorted Set commands here... if the value of `howMany` is > 0, we'll add the user to the high score table Sorted Set with [`ZADD`](https://redis.io/commands/zadd/). We're relying on a couple of useful properties of `ZADD` here:

* If the Sorted Set doesn't already exist it will create it for us.
* If the user already exists in the Sorted Set, it will update their score for us to the new value provided.

So our code for adding or updating a user in the high score table looks like this:

```javascript
if (howMany > 0) {
  await client.zAdd('scoreboard', [
    { 
      score: howMany, 
      value: userName
    }
  ]);
}
```

And if `howMany` was 0, we just need to use [`ZREM`](https://redis.io/commands/zrem/) to remove the username from the high score table (this doesn't result in an error if the high score table doesn't exist or the user isn't in it, so we don't need to check for those possibilities):

```javascript
} else {
  await client.zRem('scoreboard', userName);
}
```

Finally, let's retrieve the entire high score table and print it out in descending score order... so that the user with the most tokens comes out on top.  For this, we'll use the [`ZRANGE`](https://redis.io/commands/zrange/) command:

```javascript
console.log(await client.zRangeWithScores('scoreboard', 0, -1, {
  REV: true
}));
```

`ZRANGE` takes two zero-based index arguments... `0` being start at the first (lowest score) member in the Sorted Set, and `-1` meaning return members up to and including the last (highest score).  Passing in `true` as the value of the `REV` modifier tells Redis we want the results back in reverse order... so highest score down to lowest.

And that's all we need!  If you're building anything with Redis, or have questions we'd love to hear from you on [our Discord server](https://discord.gg/redis).
