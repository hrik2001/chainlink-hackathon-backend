# proof of concept
import requests
from web3 import Web3
import pandas as pd
import numpy as np

# section 1
# stability pool size

def get_stability_pool_size():
    '''
        returns: stability pool size in dollar
    '''
    try:
        url = "https://api.prismamonitor.com/v1/mkusd/ethereum/holders"
        response = requests.get(url)
        data = response.json()
        for holder in data["holders"]:
            if holder["label"] == "Stability Pool":
                return holder["value"]
        return None
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to retrieve stability pool value: {e}")

def get_mkUSD_circulating_supply_web3():
    abi = [
        {
            "constant": True,
            "inputs": [],
            "name": "circulatingSupply",
            "outputs": [{"name": "", "type": "uint256"}],
            "payable": False,
            "stateMutability": "view",
            "type": "function",
        },
        {
            "constant": True,
            "inputs": [],
            "name": "decimals",
            "outputs": [{"name": "", "type": "uint8"}],
            "payable": False,
            "stateMutability": "view",
            "type": "function",
        },
    ]

    w3 =  Web3(Web3.HTTPProvider('https://eth.llamarpc.com'))
    mkusd = w3.eth.contract(address='0x4591DBfF62656E7859Afe5e45f6f47D3669fBB28', abi=abi)
    circulating_supply = mkusd.functions.circulatingSupply().call()
    decimals = mkusd.functions.decimals().call()
    circulating_supply = circulating_supply / (10 ** decimals)

    return circulating_supply

def get_mkUSD_circulating_supply():
    url = "https://api.prismamonitor.com/v1/mkusd/ethereum/general"
    try:
        response = requests.get(url)
        data = response.json()
        return data["info"]["supply"]
    except requests.exceptions.RequestException as e:
        raise Exception(f"Error fetching supply data: {e}")

def get_stability_pool_size_share():
    return get_stability_pool_size()/get_mkUSD_circulating_supply()

def get_average_impact():
    # Make the API call to get the impact data
    response = requests.get('https://api.prismamonitor.com/v1/collateral/ethereum/0x7f39C581F595B53c5cb19bD0b3f8dA6c935E2Ca0/impact')
    impact_data = response.json()["impact"]

    # Calculate the average impact
    total_impact = 0
    count = 0
    for data in impact_data:
        impact = data['impact']
        if impact != 0:
            total_impact += impact
            count += 1
    try:
        average_impact = total_impact / count
    except ZeroDivisionError:
        average_impact = 0
    return average_impact

from datetime import datetime

def get_daily_ohlc():
    # Coingecko API URL
    api_url = "https://api.coingecko.com/api/v3/coins/wrapped-steth/ohlc"

    # Parameters for the API request
    params = {
        'vs_currency': 'usd',
        'days': '30'
    }

    # Make the API request
    response = requests.get(api_url, params=params)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Parse the JSON response
        ohlc_data = response.json()

        # Find the index of the first data point starting from 00:00
        start_index = next((i for i, ohlc in enumerate(ohlc_data) if datetime.utcfromtimestamp(ohlc[0] / 1000.0).strftime('%H:%M') == '00:00'), None)

        if start_index is not None:
            # Group and process the OHLC data starting from the found index
            grouped_ohlc = []
            for i in range(start_index, len(ohlc_data), 6):
                daily_data = ohlc_data[i:i+6]
                timestamp = datetime.utcfromtimestamp(daily_data[0][0] / 1000.0).strftime('%Y-%m-%d')
                open_price = daily_data[0][1]
                high_price = max(ohlc[2] for ohlc in daily_data)
                low_price = min(ohlc[3] for ohlc in daily_data)
                close_price = daily_data[-1][4]

                grouped_ohlc.append({
                    'timestamp': timestamp,
                    'open': open_price,
                    'high': high_price,
                    'low': low_price,
                    'close': close_price
                })

            # Display the grouped OHLC data
            # for data_point in grouped_ohlc:
            #     print(f"{data_point['timestamp']} - Open: {data_point['open']}, High: {data_point['high']}, Low: {data_point['low']}, Close: {data_point['close']}")
            # print(len(grouped_ohlc))
            return grouped_ohlc

        else:
            print("No data starting from 00:00 found.")

    else:
        # Print an error message if the request was not successful
        print(f"Error: {response.status_code}, {response.text}")

def calculate_ema(data, window=30):
    df = pd.DataFrame(data)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df.set_index('timestamp', inplace=True)

    # Calculate EMA
    ema = df['close'].ewm(span=window, adjust=False).mean()
    last_date_ema = ema.iloc[-1]


    return ema, last_date_ema

def calculate_parkinson_volatility(data):
    # Extract high and low prices from the OHLC data
    highs = np.array([d['high'] for d in data])
    lows = np.array([d['low'] for d in data])

    # Calculate logarithm of the ratio of high to low prices
    log_ratio = np.log(highs / lows)

    # Calculate Parkinson volatility
    parkinson_volatility = np.sqrt((1 / (4 * np.log(2))) * np.square(log_ratio))

    # Calculate the average Parkinson volatility
    average_volatility = np.mean(parkinson_volatility)

    return parkinson_volatility, average_volatility

def result():
    result_dict = {}
    # section 1
    result_dict["stability_pool_share"] = get_stability_pool_size_share()
    # section 2
    result_dict["average_impact_percent"] = get_average_impact()
    
    # section 3
    thirty_days_daily_ohlc = get_daily_ohlc()
    result_dict["volatility"] = {}
    result_dict["volatility"]["latest_ema"] = calculate_ema(thirty_days_daily_ohlc)[1]
    result_dict["volatility"]["average_parkinson"] = calculate_parkinson_volatility(thirty_days_daily_ohlc)[1]

    return result_dict