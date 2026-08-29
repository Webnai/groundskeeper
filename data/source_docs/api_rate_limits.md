# API Rate Limits — Nimbus Freight Developer Docs

*Applies to API version v3. Last updated February 2026.*

## Tiers

The Nimbus Freight API enforces rate limits per API key, based on account
tier:

- **Free tier**: 60 requests per minute, 5,000 requests per day.
- **Growth tier**: 600 requests per minute, 100,000 requests per day.
- **Enterprise tier**: 6,000 requests per minute, no daily cap.

## Exceeding the Limit

When a client exceeds its per-minute limit, the API returns an
**HTTP 429** status code along with a `Retry-After` header specifying the
number of seconds to wait before retrying. The daily cap, if exceeded,
returns an **HTTP 402** status code instead, since daily overages are
billed rather than blocked on the Growth and Enterprise tiers. Free tier
accounts that exceed the daily cap are hard-blocked until the next UTC day
boundary and are not billed.

## Burst Allowance

All tiers receive a burst allowance equal to **20% of their per-minute
limit** for a maximum of 10 seconds, to smooth out short traffic spikes
without triggering a 429. Burst usage does not count against the daily cap.

## Webhooks

Webhook delivery is retried up to **5 times** with exponential backoff
starting at 30 seconds, doubling each retry, before the webhook is marked
as failed and the customer is notified by email.
