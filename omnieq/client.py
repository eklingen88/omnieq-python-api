from .httpapi import HttpApi
from .utils.symbol_funcs import explode_option_symbol
import pandas as pd
from joblib import Parallel, delayed
from numpy import dtype


class Client:
    api = HttpApi()

    class InvalidChain(IndexError):
        pass

    @staticmethod
    def set_token(token):
        Client.api = HttpApi(token)

    @staticmethod
    def chain_expirations(symbol):
        result = Client.api.historical_chains_expirations(symbol)
        df = pd.DataFrame.from_dict(result)
        return df

    @staticmethod
    def chain_archive_dates(symbol, expiry):
        result = Client.api.historical_chains_archived(symbol, expiry)

        if len(result) == 0:
            raise Client.InvalidChain(
                f'No options chain found for {symbol} expiring on {expiry}.  Try using Client.chain_expirations(symbol) to find valid expirations.')

        return result

    @staticmethod
    def chain_eod(symbol, expiry, date=None):
        if date is None:
            date = Client.chain_archive_dates(symbol, expiry)[0]

        result = Client.api.historical_chains(symbol, expiry, date)

        df = pd.DataFrame.from_dict(result)

        df['eod_date'] = date

        df = df.astype({
            'eod_date': str,
            'symbol': str,
            'expiry': str,
            'type': str,
            'strike': 'float',
            'lastPrice': 'float',
            'bidPrice': 'float',
            'askPrice': 'float',
            'bidSize': 'int',
            'askSize': int,
            'volume': int,
            'openInterest': int,
            'impliedVolatility': float,
            'delta': float,
            'theta': float,
            'gamma': float,
            'vega': float,
            'rho': float,
        })

        return df

    @staticmethod
    def chain_eods(symbol, expirations, day_limit=30):
        """
        Get multiple EOD reports for a chain by a specific expiry.
        :param symbol: underlying symbol
        :param expirations: [YYYY-MM-DD]
        :param day_limit: None to get all
        :return:
        """
        if not isinstance(expirations, list):
            expirations = [expirations]

        _dfs = []

        for expiry in expirations:
            dates = Client.chain_archive_dates(symbol, expiry)

            if day_limit is not None:
                dates = dates[:day_limit]

            inputs = list(zip([symbol] * len(dates), [expiry] * len(dates), dates))

            # the parallel way
            results = Parallel(n_jobs=5, prefer='threads')(delayed(Client.chain_eod)(s, e, d) for s, e, d in inputs)

            # # the "classic" way
            # results = []
            #
            # for s, e, d in inputs:
            #     results.append(
            #         Client.chain_eod(s, e, d)
            #     )

            _df = pd.concat(results)

            _df = _df.sort_values(
                by=['eod_date', 'symbol'],
                ascending=True,
            )

            _df = _df.reset_index(drop=True)

            _df['eod_date'] = pd.to_datetime(_df['eod_date'])

            _dfs.append(_df)

        _df = pd.concat(_dfs)

        _df = _df.sort_values(
            by=['symbol', 'eod_date'],
            ascending=[True, True]
        ).set_index(['symbol', 'eod_date'])

        return _df

    @staticmethod
    def option_ohlcv_minutes(option_symbols, day_limit=30):
        dfs = []

        if not isinstance(option_symbols, list):
            option_symbols = [option_symbols]

        for option_symbol in option_symbols:
            exploded = explode_option_symbol(option_symbol).iloc[0]
            symbol = exploded['symbol']
            underlying_symbol = exploded['underlying_symbol']
            expiry = exploded['expiry'].isoformat()

            dates = Client.chain_archive_dates(underlying_symbol, expiry)

            if day_limit is not None:
                dates = dates[:day_limit]

            inputs = list(zip([symbol] * len(dates), dates))

            # the parallel way
            results = Parallel(n_jobs=5, prefer='threads')(delayed(HttpApi.historical_prices)(s, d) for s, d in inputs)

            valid_results = [pd.DataFrame.from_dict(i) for i in results if i is not None]

            if len(valid_results):
                df = pd.concat(valid_results)
                df = df.reset_index(drop=True)

                df['symbol'] = option_symbol

                df = df.astype({
                    'start': dtype('str'),
                    'end': dtype('str'),
                    'low': dtype('float64'),
                    'high': dtype('float64'),
                    'open': dtype('float64'),
                    'close': dtype('float64'),
                    'volume': dtype('int64'),
                    'VWAP': dtype('float64'),
                    'symbol': dtype('str')
                })

                df['start'] = pd.to_datetime(df['start'], utc=True)
                df['end'] = pd.to_datetime(df['end'], utc=True)

                df['start'] = df['start'].dt.tz_convert('America/New_York')
                df['end'] = df['end'].dt.tz_convert('America/New_York')

                df['date'] = df['end']

                df = df.set_index(['symbol', 'date'])

                dfs.append(df)

        if len(dfs):
            return pd.concat(dfs)
        else:
            return pd.DataFrame()

    @staticmethod
    def latest_chains(symbol, expirations):
        inputs = zip([symbol] * len(expirations), expirations)

        results = Parallel(n_jobs=5, prefer='threads')(delayed(HttpApi.latest_chains)(s, e) for s, e in inputs)

        valid_results = [pd.DataFrame.from_dict(i) for i in results if i is not None]

        if len(valid_results):
            df = pd.concat(valid_results)

        # df = pd.DataFrame.from_dict(res)

            df = df.astype({
                'symbol': dtype('str'),
                'expiry': dtype('str'),
                'type': dtype('str'),
                'strike': dtype('float'),
                'lastPrice': dtype('float'),
                'bidPrice': dtype('float'),
                'askPrice': dtype('float'),
                'bidSize': dtype('int'),
                'askSize': dtype('int'),
                'volume': dtype('int'),
                'openInterest': dtype('int'),
                'impliedVolatility': dtype('float'),
                'delta': dtype('float'),
                'theta': dtype('float'),
                'gamma': dtype('float'),
                'vega': dtype('float'),
                'rho': dtype('float'),
                'updated': dtype('str')
            })

            return df
        else:
            return None

    # @staticmethod
    # def option_ohlcv_daily(option_symbols, day_limit=30):
    #     from .utils.pd_funcs import resample_options_ohlcv_daily
    #     import pandas_market_calendars as mcal
    #
    #     if not isinstance(option_symbols, list):
    #         option_symbols = [option_symbols]
    #
    #     _dfs = []
    #
    #     for option_symbol in option_symbols:
    #         _df = Client.option_ohlcv_minutes(option_symbol, day_limit)
    #
    #         if _df.size == 0:
    #             break
    #
    #         _df = _df.reset_index()
    #         _df = resample_options_ohlcv_daily(_df)
    #
    #         _df['date'] = pd.to_datetime(_df['date'])
    #         start = _df['date'].min()
    #         end = _df['date'].max()
    #
    #         cal = mcal.get_calendar('NYSE')
    #
    #         df_schedule = cal.schedule(start, end, tz='America/New_York')
    #         df_schedule['date'] = pd.to_datetime(df_schedule.index)
    #
    #         _df = pd.merge(
    #             _df, df_schedule,
    #             left_on='date', right_on='date',
    #             how='left',
    #         ).dropna(subset=['market_open'])
    #
    #         _dfs.append(_df)
    #
    #
    #     _df = pd.concat(_dfs)
    #     _df = _df.set_index(['symbol', 'date'])
    #
    #     _df['days_to_expiration'] = days_until(_df, start_col='market_close', end_col='expiry_datetime')
    #
    #     return _df


    # @staticmethod
    # def option_report(option_symbols, day_limit = 30):
    #     df1 = Client.option_ohlcv_daily(option_symbols, day_limit)
    #     df1 = df1.reset_index()
    #     df1 = df1.sort_values(by=['date', 'symbol'])
    #
    #     from .utils import symbol_funcs
    #     x_symbols = symbol_funcs.explode_option_symbol(option_symbols)
    #     symbols = list(x_symbols['underlying_symbol'].unique())
    #     expirations = list(x_symbols['expiry'].unique())
    #
    #
    #     df2 = Client.chain_eods(symbols, expirations, day_limit)
    #     df2 = df2.reset_index()
    #     df2 = df2.sort_values(by=['eod_date', 'symbol'])
    #     df2 = df2.drop(columns=['volume', 'expiry'])
    #
    #     df3 = pd.merge_asof(
    #         df1, df2,
    #         left_on=['date'],
    #         right_on=['eod_date'],
    #         left_by=['symbol'], right_by=['symbol'],
    #     ).sort_values(
    #         by=['symbol', 'date']
    #     ).set_index(['symbol', 'date'])
    #
    #     return df3

    # @staticmethod
    # def all_latest_chains(symbol):
    #     expirations = Client.chain_expirations(symbol)
    #
    #     from .utils.pd_funcs import filter_future
    #
    #     expirations = filter_future(expirations, 'expiry')
    #     expirations = expirations['expiry'].values
    #
    #     inputs = list(zip([symbol] * len(expirations), expirations))
    #
    #     results = Parallel(n_jobs=5, prefer='threads')(delayed(HttpApi.latest_chains)(s, e) for s, e in inputs)
    #
    #     valid_results = [pd.DataFrame.from_dict(i) for i in results if i is not None]
    #
    #     if len(valid_results):
    #         df = pd.concat(valid_results)
    #
    #         return df

