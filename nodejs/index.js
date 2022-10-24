import { createClient } from 'redis';

const REDIS_URL = process.env.REDIS_URL || 'redis://localhost:6379';

const client = createClient({
  url: REDIS_URL
});
await client.connect();

const subClient = client.duplicate();
await subClient.connect();

await subClient.pSubscribe('__keyspace@0__:tokens:*', async (message, channel) => {
  console.log(`event >>> ${message} on ${channel}`);
  const affectedKey = channel.substring('__keyspace@0__:'.length);
  const howMany = await client.sCard(affectedKey);
  console.log(`Set cardinality ${affectedKey} is ${howMany}`);

  const userName = affectedKey.split(':')[1];

  if (howMany > 0) {
    await client.zAdd('scoreboard', [
      { 
        score: howMany, 
        value: userName
      }
    ]);
  } else {
    await client.zRem('scoreboard', userName);
  }

  console.log('Scores:');
  console.log(await client.zRangeWithScores('scoreboard', 0, -1, {
    REV: true
  }));
});