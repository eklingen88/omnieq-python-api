import pandas as pd


def prefix_columns(df: pd.DataFrame, col_prefix: str) -> pd.DataFrame:
    _df = df.copy()
    _df.columns = [f'{col_prefix}{col}' if col[:len(col_prefix)] != col_prefix else col for col in df.columns]
    return _df


def join(
        left: pd.DataFrame, right: pd.DataFrame,
        drop=False,
        left_prefix='', right_prefix=''
):
    _left = left.copy()
    _right = right.copy()

    if not isinstance(_right, pd.DataFrame) or not isinstance(_left, pd.DataFrame):
        left_type = type(_left)
        right_type = type(_right)
        raise ValueError(f'Both left and right must be dataframes.  (left is {left_type}, right is {right_type})')

    if drop:
        cols_to_drop = [col for col in _right.columns if col in _left.columns]
        cols_to_drop

        _right = _right.drop(columns=cols_to_drop)

    if left_prefix:
        _left = prefix_columns(_left, left_prefix)
    if right_prefix:
        _right = prefix_columns(_right, right_prefix)

    df = _left.join(_right)

    return df


def filter_future(df: pd.DataFrame, col: str) -> pd.DataFrame:
    _df = df.copy()

    future_mark = pd.to_datetime(_df[col]) > pd.Timestamp.now()

    _df = _df[future_mark]

    return _df


def filter_past(df: pd.DataFrame, col: str) -> pd.DataFrame:
    _df = df.copy()

    past_mask = pd.to_datetime(_df[col]) <= pd.Timestamp.now()

    _df = _df[past_mask]

    return _df


def days_until(df: pd.DataFrame,
               start_col: str = None, end_col: str = None,
               start_now: bool = True, end_now: bool = True
               ) -> pd.DataFrame:
    """
    Determine number of days (with decimal places) between start and end datet/datetimes (eg. end - start).
    :param df:
    :param start_col: If not set, the current datetime is used.
    :param end_col: If not set, the current datetime is used.
    :param start_now: By default, fills with current datetime.  Ignored if start_col is set.  Exists to make code clear.
    :param end_now: By default, fills with current datetime.  Ignored if end_col is set.  Exists to make code clear.
    :return:
    """
    if start_col is not None and start_col not in df.columns:
        raise IndexError(f'"{start_col}" not found in the dataframe and cannot be used as start_col.')
    if end_col is not None and end_col not in df.columns:
        raise IndexError(f'"{end_col}" not found in the dataframe and cannot be used as end_col.')

    if start_col is None:
        _start = pd.Timestamp.now()
    else:
        _start = pd.to_datetime(df[start_col])

    if end_col is None:
        _end = pd.Timestamp.now()
    else:
        _end = pd.to_datetime(df[end_col])

    _timedelta = _end - _start
    _oneday = pd.to_timedelta('1 day')
    _daysuntil = _timedelta / _oneday

    _df = pd.DataFrame({
        'days_until': _daysuntil
    }, index=df.index)

    return _df


def convert_to_market_tz(df: pd.DataFrame):
    _df = df.copy()

    notz_columns = _df.select_dtypes(include=['datetime64']).columns
    tz_columns = _df.select_dtypes(include=['datetime64tz']).columns

    _df[notz_columns] = _df[notz_columns].apply(lambda x: x.dt.tz_localize('America/New_York'))
    _df[tz_columns] = _df[tz_columns].apply(lambda x: x.dt.tz_convert('America/New_York'))

    return _df

def option_expirations_with_time(df, expiry_col: str = 'expiry', new_col: str = None):
    if new_col is None:
        new_col = f'{expiry_col}_datetime'
    _df = df.copy()

    expiry = _df[expiry_col]
    expiry = pd.to_datetime(expiry)
    expiry = expiry.dt.tz_localize('America/New_York')
    expiry = expiry + pd.to_timedelta('17 hours')

    _df[new_col] = expiry

    return _df



def options_ohlcv_expand(df):
    from .symbol_funcs import explode_option_symbol

    _df = df.copy()

    df_symbols = explode_option_symbol(_df['symbol'])

    _df = join(_df, df_symbols, drop=True)

    _df = option_expirations_with_time(_df)
    _df = convert_to_market_tz(_df)

    _df['days_to_expiration'] = days_until(_df, start_col='end', end_col='expiry_datetime')

    return _df


def resample_options_ohlcv_daily(df):
    _df = df.copy()

    _df['VWAP_x_volume'] = _df['VWAP'] * _df['volume']

    _df['date'] = pd.to_datetime(_df['start'])

    _df = _df.set_index('date', drop=True).resample('D').agg({
        'symbol': 'first',

        'start': 'first',
        'end': 'last',

        'low': 'min',
        'high': 'max',
        'open': 'first',
        'close': 'last',
        'volume': 'sum',

        'VWAP_x_volume': 'sum',
    })

    _df['VWAP'] = _df['VWAP_x_volume'] / _df['volume']
    _df = _df.drop(columns=['VWAP_x_volume'])

    _df['est_price'] = _df['VWAP'].interpolate()
    _df['est_price'] = (_df['est_price'] + _df['high'] + _df['low'] + _df['close']) / 4
    _df['est_price'] = _df['est_price'].interpolate()

    _df['symbol'] = _df['symbol'].ffill().bfill()

    # _df['start'] = pd.to_datetime(_df.index) + pd.to_timedelta('9 hours')
    # _df['end'] = pd.to_datetime(_df.index) + pd.to_timedelta('16 hours')

    _df.index.name = 'date'
    _df = _df.reset_index(drop=False)
    _df['date'] = _df['date'].dt.date

    _df = options_ohlcv_expand(_df)

    _df = _df.drop(columns=['start', 'end'])

    return _df

#  TODO decide what to do with this
# def add_market_open_close(df):
#     eod_datetime = df['eod_date']
#     eod_datetime = pd.to_datetime(eod_datetime)
#     eod_datetime = eod_datetime.dt.tz_localize('America/New_York')
#     eod_datetime = eod_datetime + pd.to_timedelta('16 hours')
#     df['eod_datetime'] = pd.to_datetime(eod_datetime)
#
#
#     expiry_datetime = df['expiry']
#     expiry_datetime = pd.to_datetime(expiry_datetime)
#     expiry_datetime = expiry_datetime.dt.tz_localize('America/New_York')
#     expiry_datetime = expiry_datetime + pd.to_timedelta('17 hours')
#     df['expiry_datetime'] = pd.to_datetime(expiry_datetime)
