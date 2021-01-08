import requests
from ratelimit import limits, sleep_and_retry, RateLimitException
from getpass import getpass
from diskcache import FanoutCache
from datetime import timedelta, date


class HttpApi:
    token = ''
    base_url = 'https://omnieq.com'
    cached = FanoutCache().memoize

    def __init__(self, token=None):
        if token is not None:
            HttpApi.token = token

    @staticmethod
    def input_user_token(token=None):
        if token is not None:
            HttpApi.token = token
        else:
            pass
            # HttpApi.token = getpass('Enter your OmniEQ token: ')

    @staticmethod
    @cached(name='omnieq__requests_get', expire=15)
    @sleep_and_retry
    @limits(calls=10, period=1)
    def requests_get(path: str, params: dict = {}):
        if 'token' not in params.keys():
            if HttpApi.token is None or len(HttpApi.token) == 0:
                HttpApi.input_user_token()

            params['token'] = HttpApi.token

        # print(params['token'])

        result = requests.get(HttpApi.base_url + path, params)

        if result.status_code != 200:
            raise ConnectionError(result.reason)

        json_data = result.json()

        if 'status' in json_data:
            status_message = json_data['message']

            if status_message == 'Invalid access token':
                HttpApi.token = None

            if status_message == '10 requests per second rate limit exceeded':
                raise RateLimitException(status_message, 1)

        return json_data

    @staticmethod
    @cached(name='omnieq__historical__chains__expirations', expire=1)
    def historical_chains_expirations(symbol: str):
        result = HttpApi.requests_get('/api/historical/chains/expirations', params={
            'symbol': symbol
        })

        return result

    @staticmethod
    @cached(name='omnieq__historical__chains')
    def historical_chains(symbol: str, expiry: str, date: str):
        """
        EOD options report for symbol/expiry chain by date.
        :param symbol: underlying symbol
        :param expiry: YYYY-MM-DD
        :param date: YYYY-MM-DD
        :return dict:
        """

        # TODO make sure date is in the future (will prevent caching bad data)

        result = HttpApi.requests_get('/api/historical/chains', params={
            'symbol': symbol,
            'expiry': expiry,
            'date': date,
        })

        return result

    @staticmethod
    @cached(name='omnieq__historical__chains__archived',
            expire=60 * 60 * 12)  # cached for 12 hours, doesn't change often
    def historical_chains_archived(symbol: str, expiry: str) -> [str]:
        """
        Parameters:
        symbol: stock or option symbol
        expiry: YYYY-MM-DD
        """
        result = HttpApi.requests_get('/api/historical/chains/archived', params={
            'symbol': symbol,
            'expiry': expiry
        })

        return result

    @staticmethod
    @cached(name='omnieq__historical__prices')
    def historical_prices(symbol: str, start: date = None, end: date = None):
        """
        Parameters:
        symbol: stock or option symbol
        start: YYYY-MM-DD, default to yesterday
        end: YYYY-MM-DD, default to start
        """
        if start is None:
            start = (date.today() - timedelta(days=1)).isoformat()
        if end is None:
            end = start

        if start > end:
            raise ValueError('start date must be before or equal to end date')

        if date.fromisoformat(end) - date.fromisoformat(start) > timedelta(days=30):
            raise ValueError('cannot request more than 30 days of data at a time')

        result = HttpApi.requests_get('/api/historical/prices', params={
            'symbol': symbol,
            'start': start,
            'end': end
        })

        if len(result) == 0:
            return None
        else:
            return result

    @staticmethod
    @cached(name='omnieq__symbols__optionable', expire=60 * 60 * 24)
    def symbols_optionable():
        result = HttpApi.requests_get('/api/symbols/optionable')

        return result

    @staticmethod
    @cached(name='omnieq__latest__chains', expire=15)
    def latest_chains(symbol, expiry):
        result = HttpApi.requests_get('/api/latest/chains', params={
            'symbol': symbol,
            'expiry': expiry,
        })

        return result
