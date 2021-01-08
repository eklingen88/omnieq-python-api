import pandas as pd
import numpy as np

option_symbol_pattern = r"^(?P<underlying_symbol>[A-Z]+)(?P<expire_day>\d{1,2})(?P<expire_month>[A-Z][a-z]{2})(?P<expire_year>\d{2})(?P<contract_type>C|P)(?P<strike_price>[\d\.]+)$"


def explode_option_symbol(symbol):
    symbol = np.array(symbol)

    df = pd.DataFrame({
        'symbol': symbol
    }, index=range(symbol.size))

    df = df['symbol'].str.extract(option_symbol_pattern)

    df['symbol'] = symbol
    df['expiry'] = pd.to_datetime(df['expire_day'] + df['expire_month'] + df['expire_year'])
    df['expiry'] = df['expiry'].dt.tz_localize('America/New_York')
    df['expiry'] = df['expiry'].dt.date

    df = df.drop(
        columns=['expire_day', 'expire_month', 'expire_year']
    )

    # df['expiry'] = pd.to_datetime(df['expiry'])  # + pd.to_timedelta('17h')
    df['strike_price'] = df['strike_price'].astype('float')

    return df
    # if df.index.size > 1:
    #     return df
    # else:
    #     return df.iloc[0]
