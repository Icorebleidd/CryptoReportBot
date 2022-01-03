import requests
import json
import time
import schedule
import easygui
from datetime import datetime


apiKey = easygui.enterbox("Enter your CoinMarketCap API Key")


class Bot:
    def __init__(self):
        self.url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
        self.params = {"convert": "USD"}
        self.headers = {
            "Accepts": "application/json",
            "X-CMC_PRO_API_KEY": apiKey,
        }
        self.date = datetime.today().strftime("%Y-%m-%d")  # Datetime formatting
        self.orderDict = {}
        self.percentageCoinDict = {}
        self.coinPrice = 0
        self.coinPriceVolume = 0

    # Get data from CMC API while checking for errors
    def fetchCurrenciesData(self):
        r = requests.get(url=self.url, headers=self.headers, params=self.params).json()
        if r["status"]["error_message"] != None:
            print(r["status"]["error_message"])
            quit()
        return r["data"]

    # Write data on JSON file
    def writeJSON(self, data):
        with open(f"{self.date}.json", "a", encoding="utf-8") as outfile:
            json.dump(data, outfile, ensure_ascii=False)
            outfile.write("\n")

    # Define if it's a stablecoin
    def notStableCoin(self, alldict):
        for tags in alldict["tags"]:
            if tags == "stablecoin":
                return False
        return True

    # Convert list to dictionary
    def Convert(self, a):
        it = iter(a)
        res_dct = dict(zip(it, it))
        return res_dct


reportBot = Bot()


def job():

    currencies = reportBot.fetchCurrenciesData()
    bestVolumeCurrency = None
    i = 0  # Variable used for the < 20 loop
    orderValue = sum(reportBot.orderDict.values())  # Sum of orderDict dictionary values
    newOrderValue = 0  # Reset of newOrderValue

    for currency in currencies:
        if (
            orderValue != 0
        ):  # Enter only if there's coins inside, never enter in the first program run
            for orders in reportBot.orderDict:
                if currency["symbol"] == orders:
                    newOrderValue += currency["quote"]["USD"][
                        "price"
                    ]  # New updated value
        if i < 20 and reportBot.notStableCoin(currency):  # Exclude stablecoins
            reportBot.coinPrice += currency["quote"]["USD"]["price"]
            reportBot.orderDict[currency["symbol"]] = currency["quote"]["USD"][
                "price"
            ]  # Populate dictionary
            i += 1
        if currency["quote"]["USD"][
            "volume_24h"
        ] > 76000000 and reportBot.notStableCoin(currency):
            reportBot.coinPriceVolume += currency["quote"]["USD"]["price"]
        if (
            not bestVolumeCurrency
            or currency["quote"]["USD"]["volume_24h"]
            > bestVolumeCurrency["quote"]["USD"]["volume_24h"]
        ):
            if reportBot.notStableCoin(currency):
                bestVolumeCurrency = currency
        percentChange = currency["quote"]["USD"]["percent_change_24h"]
        reportBot.percentageCoinDict[currency["symbol"]] = round(percentChange, 2)
    reportBot.percentageCoinDict = sorted(
        reportBot.percentageCoinDict.items(), key=lambda x: x[1], reverse=True
    )  # Sort dictionary by values

    # Rounding and slicing
    roundedBestVolumeCurrency = round(
        bestVolumeCurrency["quote"]["USD"]["volume_24h"], 2
    )
    roundedCoinPrice = round(reportBot.coinPrice, 2)
    roundedCoinPriceVolume = round(reportBot.coinPriceVolume, 2)
    top10 = reportBot.percentageCoinDict[0:10]
    last10 = reportBot.percentageCoinDict[-10:]

    # Writing data into JSON file
    reportBot.writeJSON(
        f"The highest volume 24h cryptocurrency is: {bestVolumeCurrency['symbol']} with a volume of: {f'{roundedBestVolumeCurrency:,}'} $"
    )
    reportBot.writeJSON(
        f"Top 10 cryptocurrencies by percentage increase the last 24h: {top10}"
    )
    reportBot.writeJSON(
        f"Top 10 cryptocurrencies by percentage decrease the last 24h: {last10[::-1]}"
    )
    reportBot.writeJSON(
        f"Money needed to buy one unit of each of the top 20 cryptocurrencies: {f'{roundedCoinPrice:,}'} $"
    )
    reportBot.writeJSON(
        f"Money needed to buy one unit of each of the cryptocurrencies with daily volume > 76.000.000 $: {f'{roundedCoinPriceVolume:,}'} $"
    )
    if orderValue != 0:  # Skip writing in the first program run
        roundedCoinPercentage = round(
            ((newOrderValue - orderValue) / orderValue) * 100, 2
        )
        reportBot.writeJSON(
            f"The percentage of gain or loss you would have made if you had bought one unit of each of the top 20 cryptocurrencies: {roundedCoinPercentage}%"
        )

    # Variable resetting
    reportBot.percentageCoinDict = reportBot.Convert(
        reportBot.percentageCoinDict
    )  # Convert from list back to dictionary
    reportBot.percentageCoinDict.clear()
    reportBot.coinPrice = 0
    reportBot.coinPriceVolume = 0
    print(
        "Done! Report created."
        + "\n"
        + str(datetime.today().strftime("%Y-%m-%d %H:%M"))
    )


schedule.every().day.at("12:30").do(job)  # Every day at 12:30pm
# schedule.every(30).seconds.do(job) # Quicker job if needed for testing
schedule.run_all()  # Start the job on the first run

while True:
    schedule.run_pending()
    time.sleep(1)
