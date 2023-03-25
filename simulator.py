from typing import Dict, List
import pandas as pd
from main import Order, OrderDepth, Trade, TradingState, Trader
import sys
sys.stdout = open('output.txt','wt')

day = pd.read_csv(".\Historical Data\Day 2\prices_round_3_day_2.csv", sep = ";")

print(day)
rowCount = len(day.index)
index = 0
time = 0
positions = {}
PnL = {}
for x in ("BANANAS", "PEARLS", "PINA_COLADAS", "COCONUTS", "DIVING_GEAR", "BERRIES", "DOLPHIN_SIGHTINGS"): 
    PnL[x] = 0
    positions[x] = 0

while True:
    order_depths : Dict[str, OrderDepth]
    order_depths = {}
    while time == day["timestamp"][index]:
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
    state = TradingState(time, {}, order_depths, {"ownTrades":0}, {"marketTrades":0}, {"Position":0}, {})
    simulation = Trader()
    simorders = simulation.run(state)
    


    #sim orders
    for x in positions.keys():
        for y in simorders[x]:
            if y.quantity > 0:
                for z in sorted(order_depths[x].sell_orders.keys()):
                    if y.price >= z:
                        if y.quantity <= order_depths[x].sell_orders[z]:
                            positions[x] += y.quantity
                            order_depths[x].sell_orders[z] -= y.quantity
                        else:
                            positions[x] += order_depths[x].sell_orders[z]
                            del order_depths[x].sell_orders[z]
                            #add rest of trade to book
            else:
                for z in order_depths[x].buy_orders.keys():
                    if y.price <= z:
                        if y.quantity <= order_depths[x].buy_orders[z]:
                            positions[x] += y.quantity
                            order_depths[x].buy_orders[z] -= y.quantity
                        else:
                            positions[x] += order_depths[x].buy_orders[z]
                            del order_depths[x].buy_orders[z]
                            #add rest of trade to book

    
    
    
    time += 100
    print(time)
    
        




