from typing import Dict, List
import pandas as pd
from main import Order, OrderDepth, Trade, TradingState, Trader
import sys
sys.stdout = open('output.txt','wt')

day = pd.read_csv(".\Historical Data\Day 2\prices_round_3_day_2.csv", sep = ";")
index = 0
market = {}
time = 0

rowCount = len(day.index)
index = 0
time = 0
positions = {}
Realized = {}
Unrealized = {}
Midprice = {}
PnL = {}
for x in ("BANANAS", "PEARLS", "PINA_COLADAS", "COCONUTS", "DIVING_GEAR", "BERRIES", "DOLPHIN_SIGHTINGS"): 
    Midprice[x] = 0
    Realized[x] = 0 
    Unrealized[x] = 0
    PnL[x] = 0
    positions[x] = 0

simulation = Trader()
finalcsvoutput = ""

while True:
    order_depths : Dict[str, OrderDepth]
    order_depths = {}
    while index < rowCount and time == day["timestamp"][index]:
        Midprice[day["product"][index]] = day["mid_price"][index]
        Depth = OrderDepth()
        for x in ((day["bid_price_1"][index], day["bid_volume_1"][index]), (day["bid_price_2"][index], day["bid_volume_2"][index]), (day["bid_price_3"][index], day["bid_volume_3"][index])):
            if not(pd.isna(x[0])):
                Depth.buy_orders[x[0]] = x[1]
        for x in ((day["ask_price_1"][index], day["ask_volume_1"][index]), (day["ask_price_2"][index], day["ask_volume_2"][index]), (day["ask_price_3"][index], day["ask_volume_3"][index])):
            if not(pd.isna(x[0])):
                Depth.sell_orders[x[0]] = x[1]
        order_depths[day["product"][index]] = Depth
        index += 1
        if index == rowCount: break
    if time == 1000000: break
    state = TradingState(time, {}, order_depths, {}, {}, positions, {})
    simorders = simulation.run(state)
    
    market : Dict[int, Dict[str, Dict[int, int]]]

    #sim orders
    for x in simorders.keys():
        buyorders = []
        sellorders = []
        for y in simorders[x]:
            if y.quantity > 0:
                for z in sorted(order_depths[x].sell_orders.keys()):
                    if y.price >= z:
                        if y.quantity <= order_depths[x].sell_orders[z]:
                            positions[x] += y.quantity
                            Realized[x] += y.quantity * y.price
                            order_depths[x].sell_orders[z] -= y.quantity

                        else:
                            positions[x] += order_depths[x].sell_orders[z]
                            Realized[x] += order_depths[x].sell_orders[z] * y.price
                            del order_depths[x].sell_orders[z]
                            # buyorders.append({y.price : [y.quantity - order_depths[x].sell_orders[z], True]})
                            #add rest of trade to book
            else:
                for z in order_depths[x].buy_orders.keys():
                    if y.price <= z:
                        if y.quantity <= order_depths[x].buy_orders[z]:
                            positions[x] += y.quantity
                            Realized[x] += y.quantity * y.price
                            order_depths[x].buy_orders[z] -= y.quantity
                        else:
                            positions[x] += order_depths[x].buy_orders[z]
                            Realized[x] += order_depths[x].buy_orders[z] * y.price
                            del order_depths[x].buy_orders[z]
        Unrealized[x] = positions[x] * Midprice[x]
        PnL[x] = Realized[x] + Unrealized[x]
        finalcsvoutput += ";" + str(time) + ";" + x + ";;;;;;;;;;;;;" + str(PnL[x]) + "\n"
    time += 100
    print(time)
print("\n\n\n\n\n\n\n")
print(finalcsvoutput)