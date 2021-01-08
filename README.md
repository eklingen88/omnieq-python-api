# OmniEQ API Client

## Purpose

This library is intended to serve as a simplified interface for the [OmniEQ](https://omnieq.com/) API.

Detailed documentation on how to use the API can be found [here](https://omnieq.com/about).

## Installation

Package available from [source](https://github.com/eklingen88/omnieq-python-api) or [PyPi](https://pypi.org/project/omnieq-api/).

```
pip install omnieq-api
```

## Usage

Please see _notebook/usage.ipynb_.

## Features

### Cache

Historical data is cached on disk indefinitely using the [_disckcache_](https://pypi.org/project/diskcache/) library. I felt it was safe to say what happened last week isn't going to change any time soon. (and if you figure out how, let me know)

This allows for quicker response times and avoids repeat requests.

Latest chains are cached for 15 seconds and chain expirations for 12 hours.  For the most part, everything historical doesn't expire.


### Rate Limit

Rate limiting is built-in with the ratelimit library. It adheres (near) to the rate limit specified in the docs. 

The limit may need to be adjusted if rate limit errors are being returned by the server. 


### Parallel Requests

With a rate limit of 10/s and each request taking me 0.7 seconds on a single thread (shitty wifi), I figured it'd be smart to parallelize them (duh).

So this has been built into some functions like _Client.option_ohlcv_minute_, which will aggregate a full history of an option (first checking archive dates, then requesting historical prices for each).

## Roadmap

* Issues (below)
* Token management (validate token, create pickle file, don't ask again)
* Complete API coverage (the spread builder is going to be some work)
* API error response handling
* ... documentaion (bleh)

## Issues

* Requesting historical data for prices in the future (which will obviously have no results) will be permanently cached. 