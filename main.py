from typing import Dict, List

import json
from json import JSONEncoder

Time = int
Symbol = str
Product = str
Position = int
UserId = str
Observation = int


class Listing:
    def __init__(self, symbol: Symbol, product: Product, denomination: Product):
        self.symbol = symbol
        self.product = product
        self.denomination = denomination


class Order:
    def __init__(self, symbol: Symbol, price: int, quantity: int) -> None:
        self.symbol = symbol
        self.price = price
        self.quantity = quantity

    def __str__(self) -> str:
        return "(" + self.symbol + ", " + str(self.price) + ", " + str(self.quantity) + ")"

    def __repr__(self) -> str:
        return "(" + self.symbol + ", " + str(self.price) + ", " + str(self.quantity) + ")"
    

class OrderDepth:
    def __init__(self):
        self.buy_orders: Dict[int, int] = {}
        self.sell_orders: Dict[int, int] = {}


class Trade:
    def __init__(self, symbol: Symbol, price: int, quantity: int, buyer: UserId = None, seller: UserId = None, timestamp: int = 0) -> None:
        self.symbol = symbol
        self.price: int = price
        self.quantity: int = quantity
        self.buyer = buyer
        self.seller = seller
        self.timestamp = timestamp

class TradingState(object):
    def __init__(self,
                 timestamp: Time,
                 listings: Dict[Symbol, Listing],
                 order_depths: Dict[Symbol, OrderDepth],
                 own_trades: Dict[Symbol, List[Trade]],
                 market_trades: Dict[Symbol, List[Trade]],
                 position: Dict[Product, Position],
                 observations: Dict[Product, Observation]):
        self.timestamp = timestamp
        self.listings = listings
        self.order_depths = order_depths
        self.own_trades = own_trades
        self.market_trades = market_trades
        self.position = position
        self.observations = observations
        
    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True)
    
class ProsperityEncoder(JSONEncoder):
        def default(self, o):
            return o.__dict__
        


class Trader:
    maxPositionQuantity: int = 20

    def run(self, state: TradingState) -> Dict[str, List[Order]]:
        """
        Only method required. It takes all buy and sell orders for all symbols as an input,
        and outputs a list of orders to be sent
        """
        # Initialize the method output dict as an empty dict
        result = {}

        # Iterate over all the keys (the available products) contained in the order depths
        for product in state.order_depths.keys():
            currentProductAmount = 0

            try:
                currentProductAmount = state.position[product]
            except:
                pass

            print("AT TIME ", state.timestamp, "PRODUCT ", product, " HAS POSITION: ", currentProductAmount)
            # if product == "BANANAS":
            #     pass
            
            # Check if the current product is the 'PEARLS' product, only then run the order logic
            if product == 'PEARLS':

                # Retrieve the Order Depth containing all the market BUY and SELL orders for PEARLS
                order_depth: OrderDepth = state.order_depths[product]

                # Initialize the list of Orders to be sent as an empty list
                orders: list[Order] = []

                # Define a fair value for the PEARLS.
                # Note that this value of 1 is just a dummy value, you should likely change it!
                acceptable_price = 10000

                # If statement checks if there are any SELL orders in the PEARLS market
                if len(order_depth.sell_orders) > 0:

                    # # Sort all the available sell orders by their price,
                    # # and select only the sell order with the lowest price
                    # best_ask = min(order_depth.sell_orders.keys())
                    # best_ask_volume = order_depth.sell_orders[best_ask]

                    # # Check if the lowest ask (sell order) is lower than the above defined fair value
                    # if best_ask <= acceptable_price:
                    #     print("AT TIME ", state.timestamp, "PRODUCT ", product, " HAS SELL ORDERS: ", state.order_depths[product].sell_orders)

                    #     # In case the lowest ask is lower than our fair value,
                    #     # This presents an opportunity for us to buy cheaply
                    #     # The code below therefore sends a BUY order at the price level of the ask,
                    #     # with the same quantity
                    #     # We expect this order to trade with the sell order
                    #     print("BUY", product, str(-best_ask_volume) + "x", best_ask)
                    #     orders.append(Order(product, best_ask, -best_ask_volume))

                    # Go through all the orders and match all favorable orders
                    print("AT TIME ", state.timestamp, "PRODUCT ", product, " HAS SELL ORDERS: ", state.order_depths[product].sell_orders)

                    # Loop through all the sell orders, but first sorted by price descending
                    # sell_orders is a dictionary with price as key and quantity as value
                    possiblePrices = sorted(order_depth.sell_orders.keys(), reverse=True)

                    for order in possiblePrices:
                        if order < acceptable_price:

                            # In case the lowest ask is lower than our fair value,
                            # This presents an opportunity for us to buy cheaply
                            # The code below therefore sends a BUY order at the price level of the ask,
                            # with the same quantity
                            # We expect this order to trade with the sell order
                            possibleQuantity: int = -1 * order_depth.sell_orders[order]
                            if possibleQuantity + currentProductAmount > self.maxPositionQuantity:
                                possibleQuantity = self.maxPositionQuantity - currentProductAmount

                            print("TRYING TO BUY", product, str(possibleQuantity) + "x", order)
                            orders.append(Order(product, order, possibleQuantity))
                            currentProductAmount += possibleQuantity # the trade will succeed, so assume it has


                # The below code block is similar to the one above,
                # the difference is that it finds the highest bid (buy order)
                # If the price of the order is higher than the fair value
                # This is an opportunity to sell at a premium
                if len(order_depth.buy_orders) != 0:
                    # best_bid = max(order_depth.buy_orders.keys())
                    # best_bid_volume = order_depth.buy_orders[best_bid]
                    # if best_bid >= acceptable_price:
                    #     print("AT TIME ", state.timestamp, "PRODUCT ", product, " HAS BUY ORDERS: ", state.order_depths[product].buy_orders)

                    #     print("SELL", product, str(best_bid_volume) + "x", best_bid)
                    #     orders.append(Order(product, best_bid, -best_bid_volume))

                    print("AT TIME ", state.timestamp, "PRODUCT ", product, " HAS BUY ORDERS: ", state.order_depths[product].buy_orders)

                    possiblePrices: list[int] = sorted(order_depth.buy_orders.keys(), reverse=False)

                    for order in possiblePrices:
                        if order > acceptable_price:

                            # In case the lowest ask is lower than our fair value,
                            # This presents an opportunity for us to buy cheaply
                            # The code below therefore sends a BUY order at the price level of the ask,
                            # with the same quantity
                            # We expect this order to trade with the sell order
                            possibleQuantity: int = -1 * order_depth.buy_orders[order] # some negative number
                            if possibleQuantity + currentProductAmount < -1 * self.maxPositionQuantity:
                                possibleQuantity = -1 * self.maxPositionQuantity - currentProductAmount

                            print("TRYING TO SELL", product, str(possibleQuantity) + "x", order)
                            orders.append(Order(product, order, possibleQuantity))
                            currentProductAmount += possibleQuantity # the trade will succeed, so assume it has

                # Add all the above orders to the result dict
                result[product] = orders


                # print("Market High", product, str(possibleQuantity) + "x", order)
                # orders.append(Order(product, order, possibleQuantity))
                # currentProductAmount += possibleQuantity




                # Return the dict of orders
                # These possibly contain buy or sell orders for PEARLS
                # Depending on the logic above
        return result
    
