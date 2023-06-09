from typing import Dict, List

import json
from json import JSONEncoder

Time = int
Symbol = str
Product = str
Position = int
UserId = str
Observation = int
Sell = 0
Buy = 1


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
    bananasSimpleMovingAverage: List[int] = []
    bananasVelocityMovingAverage: List[int] = []
    pearlsSimpleMovingAverage: List[int] = []
    pearlsVelocityMovingAverage: List[int] = []

    # CONFIGURABLE PARAMETERS
    smaSize: int = 10
    stddevThreshold: float = 0.5
    pearlGreediness: float = 0    
    # Define a fair value for the PEARLS.
    pearl_acceptable_price = 10000
    # ignored for now
    bananasQuantityAffinity: int = 2

    """
    Only method required. It takes all buy and sell orders for all symbols as an input,
    and outputs a list of orders to be sent
    """
    def run(self, state: TradingState) -> Dict[str, List[Order]]:
        if (len(self.bananasSimpleMovingAverage) == 0):
            print("OPERATING WITH SMASIZE ", self.smaSize, "AND STDDEVTHRESHOLD ", self.stddevThreshold, "AND PEARLGREEDINESS ", self.pearlGreediness)
        
        # Initialize the method output dict as an empty dict
        result = {}

        # Iterate over all the keys (the available products) contained in the order depths
        for product in state.order_depths.keys():
            currentProductAmount = 0

            try:
                currentProductAmount = state.position[product]
            except:
                pass

            # Initialize the list of Orders to be sent as an empty list
            orders: list[Order] = []

            # Retrieve the Order Depth containing all the market BUY and SELL orders for PEARLS
            order_depth: OrderDepth = state.order_depths[product]
            priceOne = Trader.getBestPossiblePrice(self, order_depth=order_depth, isBuying=True)
            priceTwo = Trader.getBestPossiblePrice(self, order_depth=order_depth, isBuying=False)
            avg = 0
            q = 0

            if priceOne != -1:
                avg += priceOne
                q += 1
            if priceTwo != -1:
                avg += priceTwo
                q += 1

            print("AT TIME ", state.timestamp, "PRODUCT ", product, " HAS POSITION: ", currentProductAmount)
            if product == "BANANAS":
                if len(self.bananasSimpleMovingAverage) < self.smaSize and q == 2:
                    self.bananasSimpleMovingAverage.append(avg / q)                
                elif q == 2:
                    self.bananasSimpleMovingAverage.pop(0)
                    self.bananasSimpleMovingAverage.append(avg / q)

                # if len(self.bananasSimpleMovingAverage) < self.bananasSimpleMovingAverageSize:
                #     continue

                computedAverage: int = sum(self.bananasSimpleMovingAverage) / len(self.bananasSimpleMovingAverage)
                recentStandardDeviation: float = 0
                for observation in self.bananasSimpleMovingAverage:
                    recentStandardDeviation += (observation - computedAverage) ** 2

                recentStandardDeviation = (recentStandardDeviation / len(self.bananasSimpleMovingAverage)) ** 0.5

                if len(order_depth.sell_orders) > 0:
                    print("AT TIME ", state.timestamp, "PRODUCT ", product, " HAS SELL ORDERS: ", state.order_depths[product].sell_orders)
                    possiblePrices = sorted(order_depth.sell_orders.keys(), reverse=True)

                    acceptable_buy_price = computedAverage - recentStandardDeviation * self.stddevThreshold
                    for price in possiblePrices:
                        if price < acceptable_buy_price:
                            possibleQuantity: int = -1 * order_depth.sell_orders[price] # becomes some positive number
                            if possibleQuantity + currentProductAmount > self.maxPositionQuantity:
                                print("CANNOT BUY", product, str(possibleQuantity) + "x", price, "WHEN SMA IS", computedAverage, "AND STDDEV IS", recentStandardDeviation)
                                possibleQuantity = self.maxPositionQuantity - currentProductAmount

                            if possibleQuantity > 0:
                                orders.append(Order(product, price, possibleQuantity))
                                currentProductAmount += possibleQuantity
                                print("TRYING TO BUY", product, str(possibleQuantity) + "x", price, "WHEN SMA IS", computedAverage, "AND STDDEV IS", recentStandardDeviation)
                                

                if len(order_depth.buy_orders) > 0:
                    print("AT TIME ", state.timestamp, "PRODUCT ", product, " HAS BUY ORDERS: ", state.order_depths[product].buy_orders)
                    possiblePrices = sorted(order_depth.buy_orders.keys())
                    acceptable_sell_price = computedAverage + recentStandardDeviation * self.stddevThreshold
                    for price in possiblePrices:
                        if price > acceptable_sell_price:
                            possibleQuantity: int = -1 * order_depth.buy_orders[price] # becomes some negative number
                            if possibleQuantity + currentProductAmount < -1 * self.maxPositionQuantity:
                                possibleQuantity = -1 * self.maxPositionQuantity - currentProductAmount
                                print("CANNOT SELL", product, str(possibleQuantity) + "x", price, "WHEN SMA IS", computedAverage, "AND STDDEV IS", recentStandardDeviation)
                            if possibleQuantity < 0:
                                orders.append(Order(product, price, possibleQuantity))
                                currentProductAmount += possibleQuantity
                                print("TRYING TO SELL", product, str(possibleQuantity) + "x", price, "WHEN SMA IS", computedAverage, "AND STDDEV IS", recentStandardDeviation)

                # failed attempt at market making
                # if len(order_depth.sell_orders) > 0 and len(order_depth.buy_orders) > 0:
                #     lowest_sell_price = Trader.getBestPossiblePrice(self, order_depth=order_depth, isBuying=False, offset=-1)
                #     highest_buy_price = Trader.getBestPossiblePrice(self, order_depth=order_depth, isBuying=True, offset=-1)
                #     print("AT TIME ", state.timestamp, "PRODUCT ", product, " LOWEST SELL PRICE: ", lowest_sell_price, " HIGHEST BUY PRICE: ", highest_buy_price)

                #     if (lowest_sell_price - highest_buy_price) > 2:
                #         max_could_sell = -1 * currentProductAmount - self.maxPositionQuantity # this is a negative number
                #         max_could_buy = -1 * currentProductAmount + self.maxPositionQuantity # this is a positive number
                #         amount = min(abs(max_could_sell), abs(max_could_buy))
                #         print("AT TIME ", state.timestamp, "PRODUCT ", product, " MAX COULD SELL: ", max_could_sell, " MAX COULD BUY: ", max_could_buy, " AMOUNT: ", amount)
                #         if amount > 0:
                #             midpoint = (lowest_sell_price + highest_buy_price) / 2
                #             # sell order at midpoint + 1
                #             # buy order at midpoint - 1
                #             orders.append(Order(product, midpoint + 1, -1 * amount))
                #             orders.append(Order(product, midpoint - 1, amount))

                #             print("PRODUCT", product, "BUYING AT", midpoint - 1, "SELLING AT", midpoint + 1, "AMOUNT", amount)


            # DON'T do the same for PEARLS
            # if product == 'PEARLS':
            #     if len(self.pearlsSimpleMovingAverage) < self.smaSize and q == 2:
            #         self.pearlsSimpleMovingAverage.append(avg / q)                
            #     elif q == 2:
            #         self.pearlsSimpleMovingAverage.pop(0)
            #         self.pearlsSimpleMovingAverage.append(avg / q)
            
            #     # if len(self.pearlsSimpleMovingAverage) < self.pearlsSimpleMovingAverageSize:
            #     #     continue

            #     computedAverage: int = sum(self.pearlsSimpleMovingAverage) / len(self.pearlsSimpleMovingAverage)
            #     recentStandardDeviation: float = 0
            #     for observation in self.pearlsSimpleMovingAverage:
            #         recentStandardDeviation += (observation - computedAverage) ** 2

            #     recentStandardDeviation = (recentStandardDeviation / len(self.pearlsSimpleMovingAverage)) ** 0.5

            #     if len(order_depth.sell_orders) > 0:
            #         print("AT TIME ", state.timestamp, "PRODUCT ", product, " HAS SELL ORDERS: ", state.order_depths[product].sell_orders)
            #         possiblePrices = sorted(order_depth.sell_orders.keys(), reverse=True)

            #         acceptable_buy_price = computedAverage - recentStandardDeviation * self.stddevThreshold
            #         for price in possiblePrices:
            #             if price < acceptable_buy_price:
            #                 possibleQuantity: int = -1 * order_depth.sell_orders[price] # becomes some positive number
            #                 if possibleQuantity + currentProductAmount > self.maxPositionQuantity:
            #                     possibleQuantity = self.maxPositionQuantity - currentProductAmount
            #                     print("CANNOT BUY", product, str(possibleQuantity) + "x", price, "WHEN SMA IS", computedAverage, "AND STDDEV IS", recentStandardDeviation)
            #                 if possibleQuantity > 0:
            #                     orders.append(Order(product, price, possibleQuantity))
            #                     currentProductAmount += possibleQuantity
            #                     print("TRYING TO BUY", product, str(possibleQuantity) + "x", price, "WHEN SMA IS", computedAverage, "AND STDDEV IS", recentStandardDeviation)

            #     if len(order_depth.buy_orders) > 0:
            #         print("AT TIME ", state.timestamp, "PRODUCT ", product, " HAS BUY ORDERS: ", state.order_depths[product].buy_orders)
            #         possiblePrices = sorted(order_depth.buy_orders.keys())
            #         acceptable_sell_price = computedAverage + recentStandardDeviation * self.stddevThreshold
            #         for price in possiblePrices:
            #             if price > acceptable_sell_price:
            #                 possibleQuantity: int = -1 * order_depth.buy_orders[price]
            #                 if possibleQuantity + currentProductAmount < -1 * self.maxPositionQuantity:
            #                     possibleQuantity = -1 * self.maxPositionQuantity - currentProductAmount
            #                     print("CANNOT SELL", product, str(possibleQuantity) + "x", price, "WHEN SMA IS", computedAverage, "AND STDDEV IS", recentStandardDeviation)
            #                 if possibleQuantity < 0:
            #                     orders.append(Order(product, price, possibleQuantity))
            #                     currentProductAmount += possibleQuantity
            #                     print("TRYING TO SELL", product, str(possibleQuantity) + "x", price, "WHEN SMA IS", computedAverage, "AND STDDEV IS", recentStandardDeviation)


            # Check if the current product is the 'PEARLS' product, only then run the order logic
            if product == 'PEARLS':
                

                # If statement checks if there are any SELL orders in the PEARLS market
                if len(order_depth.sell_orders) > 0:

                    # Go through all the orders and match all favorable orders
                    print("AT TIME ", state.timestamp, "PRODUCT ", product, " HAS SELL ORDERS: ", state.order_depths[product].sell_orders)

                    # Loop through all the sell orders, but first sorted by price descending
                    # sell_orders is a dictionary with price as key and quantity as value
                    possiblePrices = sorted(order_depth.sell_orders.keys(), reverse=True)

                    for price in possiblePrices:
                        if price < Trader.pearl_acceptable_price - Trader.pearlGreediness:

                            # In case the lowest ask is lower than our fair value,
                            # This presents an opportunity for us to buy cheaply
                            # The code below therefore sends a BUY order at the price level of the ask,
                            # with the same quantity
                            # We expect this order to trade with the sell order
                            possibleQuantity: int = -1 * order_depth.sell_orders[price]
                            if possibleQuantity + currentProductAmount > self.maxPositionQuantity:
                                possibleQuantity = self.maxPositionQuantity - currentProductAmount

                            print("TRYING TO BUY", product, str(possibleQuantity) + "x", price)
                            orders.append(Order(product, price, possibleQuantity))
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

                    for price in possiblePrices:
                        if price > Trader.pearl_acceptable_price + Trader.pearlGreediness:

                            # In case the lowest ask is lower than our fair value,
                            # This presents an opportunity for us to buy cheaply
                            # The code below therefore sends a BUY order at the price level of the ask,
                            # with the same quantity
                            # We expect this order to trade with the sell order
                            possibleQuantity: int = -1 * order_depth.buy_orders[price] # some negative number
                            if possibleQuantity + currentProductAmount < -1 * self.maxPositionQuantity:
                                possibleQuantity = -1 * self.maxPositionQuantity - currentProductAmount

                            print("TRYING TO SELL", product, str(possibleQuantity) + "x", price)
                            orders.append(Order(product, price, possibleQuantity))
                            currentProductAmount += possibleQuantity # the trade will succeed, so assume it has

            
            
            # Add all the above orders to the result dict            
            result[product] = orders

        return result
    

    # def buyItem(self, product, order_depth: OrderDepth, ):
    #     possibleQuantity: int = -1 * order_depth.sell_orders[order]
    #     if possibleQuantity + currentProductAmount > self.maxPositionQuantity:
    #         possibleQuantity = self.maxPositionQuantity - currentProductAmount


    #     print("TRYING TO BUY", product, str(possibleQuantity) + "x", order)
    #     orders.append(Order(product, order, possibleQuantity))
    #     possiblePrices.remove(order)
    #     currentProductAmount += possibleQuantity

    def LimitOrder(self, product, buy : int, state : TradingState, price = 0, volume = 0):
        """"Buy/Sell an item, set price/volume to 0 to ignore, returns _________"""
        orderBook = state.order_depths[product]
        currentPos = state.position[product]
        if buy:
            prices = sorted(orderBook.sell_orders.keys(), reverse=True)
            vol = 0
            # for x in prices:
            #     if price and x > price:
            #         break
            #     if volume and vol < volume:
            #       


            pass
        else:
            pass

        

    
    def getBestPossiblePrice(self, order_depth: OrderDepth, isBuying: bool, offset: int = 0) -> int:
        if isBuying:
            if len(order_depth.buy_orders) == 0:
                return -1
            possiblePrices: list[int] = sorted(order_depth.buy_orders.keys(), reverse=False)
        else:
            if len(order_depth.sell_orders) == 0:
                return -1
            possiblePrices: list[int] = sorted(order_depth.sell_orders.keys(), reverse=True)

        return possiblePrices[offset]