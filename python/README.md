## Application Setup

To setup the application, first install the dependencies:

```bash
$ cd python
$ pip install -r requirements.txt
```

The application expects to find Redis at `localhost` on port `6379` with no password.  These are the default values when installing Redis.

If your Redis server is located elsewhere and/or requires a password, set the value of the `REDIS_URL` environment variable to a valid [Redis connection URL](https://redis.readthedocs.io/en/stable/examples/connection_examples.html#Connecting-to-Redis-instances-by-specifying-a-URL-scheme.) before starting the application. For example:

```bash
$ export REDIS_URL=redis://luca:sssssh@redis.mydomain.com:6390
```

Finally, the default logging level is set to `INFO`. You can change it with the `LOGLEVEL` environment variable. For example:
```bash
$ export LOGLEVEL=DEBUG
```

## Running the Application

Start the application as follows:

```bash
$ python main.py
```
