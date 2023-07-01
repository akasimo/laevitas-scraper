import time
import json
from seleniumwire import webdriver
from seleniumwire.utils import decode
from seleniumwire.webdriver import ChromeOptions

import pandas as pd

MIN_MCAP = 10_000_000

DISPLAY_COLS = [
    "market_cap",
    "currency.value",
    "price.value",
    "change.value",
    "volume.value",
    "funding.value",
    "next_fr.value",
    "open_interest_volume.value",
    "liquidations.long",
    "liquidations.short",
    "correlation.btc.30",
    "correlation.eth.30",
]

options = ChromeOptions()
options.add_argument("--headless")

driver = webdriver.Chrome(options=options)
driver.get("https://app.laevitas.ch/altsderivs/aggregate/perpetualswaps")


start = time.time()

while time.time() - start < 60:
    matching_requests = [
        request
        for request in driver.requests
        if request.response
        and request.method == "POST"
        and "graph" in request.url
        and "getToptGainersAltsDerivsV2" in request.body.decode()
    ]
    if len(matching_requests):
        request = matching_requests[0]
        resp_str = decode(
            request.response.body,
            request.response.headers.get("Content-Encoding", "identity"),
        )
        resp = json.loads(resp_str.decode())
        data = resp["data"]["getToptGainersAltsDerivsV2"]
        df = pd.json_normalize(data)
        df = df[df.market_cap > MIN_MCAP]
        break
    else:
        time.sleep(1)
        df = pd.DataFrame()

driver.quit()

# CUSTOM COLS
df["oi_mcap_change"] = df["open_interest.change_usd"] / df["market_cap"]
df["oi_mcap"] = df["open_interest.value"] / df["market_cap"]
df["vol_mcap"] = df["volume.value"] / df["market_cap"]
df["liq_mcap"] = (df["liquidations.long"] + df["liquidations.short"]) / df["market_cap"]

ADDITIONAL_COLS = ["oi_mcap_change", "oi_mcap", "vol_mcap", "liq_mcap"]
DISPLAY_COLS.extend(ADDITIONAL_COLS)

if df.empty:
    print("No data")
else:
    for col in ADDITIONAL_COLS:
        print("Col name: ", col)
        print(df[DISPLAY_COLS].sort_values(col, ascending=False).head(10))
        print("-------------------")
a = 1
