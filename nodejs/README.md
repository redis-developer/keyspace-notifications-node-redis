## Application Setup

To setup the application, first install the dependencies:

```bash
$ cd nodejs
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
