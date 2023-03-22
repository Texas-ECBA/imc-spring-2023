from typing import Dict, List

import json
from json import JSONEncoder

Time = int
Symbol = str
Product = str
Position = int
UserId = str
Observation = int
SELL = 0
BUY = 1


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
            pass #@me - uncomment #print("OPERATING WITH SMASIZE ", self.smaSize, "AND STDDEVTHRESHOLD ", self.stddevThreshold, "AND PEARLGREEDINESS ", self.pearlGreediness)
        
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
            if product == "PEARLS": #@me - remove
                print("AT TIME ", state.timestamp, "PRODUCT ", product, " HAS POSITION: ", currentProductAmount)
            if product == "BANANAS" and False: #@me - remove false
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

                if len(order_depth.sell_orders) > 0:

                    print("AT TIME ", state.timestamp, "PRODUCT ", product, " HAS SELL ORDERS: ", state.order_depths[product].sell_orders)
                    if currentProductAmount != 20:
                        BuyOrders = self.PriceOrder(product, BUY, state, 10000, 20 - currentProductAmount, printTime=True)
                        for x in BuyOrders[0]:
                            orders.append(x)
                        currentProductAmount += BuyOrders[1][1]
                        BestSell = BuyOrders[1][3]
                    else:
                        BestSell = sorted(order_depth.sell_orders.keys(), reverse=False) [-1]


                if len(order_depth.buy_orders) != 0:

                    print("AT TIME ", state.timestamp, "PRODUCT ", product, " HAS BUY ORDERS: ", state.order_depths[product].buy_orders)
                    if currentProductAmount != -20:
                        SellOrders = self.PriceOrder(product, SELL, state, 10000, -20 - currentProductAmount, printTime = True)
                        for x in SellOrders[0]:
                            orders.append(x)
                        currentProductAmount += SellOrders[1][1]
                        BestBuy = SellOrders[1][3]
                    else:
                        BestBuy = sorted(order_depth.buy_orders.keys(), reverse=True) [-1]

                if type(BestBuy) == type(None):
                    BestBuy = 9995
                if type(BestSell) == type(None):
                    BestSell = 10005
                print("Current Market is", BestBuy, "-", BestSell)
                if BestBuy < 9999 or BestBuy < 10000 and currentProductAmount > 0:
                    BestBuy += 1
                    if currentProductAmount < 15:
                        orders.append(Order(product, BestBuy, 15-currentProductAmount))
                        print("Placed Buy order of", 15-currentProductAmount, product, "for", BestBuy)
                if BestSell > 10001 or BestSell > 10000 and currentProductAmount < 0:
                    BestSell -= 1
                    if currentProductAmount > -15:
                        orders.append(Order(product, BestSell, -15-currentProductAmount))
                        print("Placed Sell order of", -15-currentProductAmount, product, "for", BestSell)        
            
            # Add all the above orders to the result dict            
                print(".")
                print(".")
                print(".")
            result[product] = orders

        return result
    

    def VolumeOrder (self, product, buy : int, state : TradingState, volume : int, priceLimit = 0, printTime = False):
        """Trades until it hits a certain volume traded, optional min/max trading price
        Returns a list of orders made and a tuple of last price traded at, total volume traded, 
        and if it filled the final order it traded at"""
        volume = abs(volume)
        ordersMade = []
        orderBook = state.order_depths[product]
        TradeFill = True
        PriceTraded = 0
        VolumeTraded = 0
        if buy:
            prices = sorted(orderBook.sell_orders.keys(), reverse=False)
            i = 0
            while VolumeTraded < volume and i < len(prices):
                if priceLimit and prices[i] > priceLimit: break
                quantity = orderBook.sell_orders[prices[i]]
                volOrdered = quantity
                if printTime: print("volOrdered + VolumeTraded > volume:", volOrdered + VolumeTraded > volume)
                if (volOrdered + VolumeTraded > volume): 
                    volOrdered = volume - VolumeTraded
                    TradeFill = False
                    if printTime: print("volOrdered = volume - VolumeTraded:", volOrdered)
                print("BUYING", product, str(volOrdered) + "x", prices[i])
                ordersMade.append(Order(product, prices[i], volOrdered))
                VolumeTraded += volOrdered
                PriceTraded = prices[i]
                i += 1
            if not(TradeFill): nextBest = PriceTraded
            elif i < len(prices): nextBest = prices[i]
            else: nextBest = None
            

            return ordersMade, (PriceTraded, VolumeTraded, TradeFill, nextBest)
        else:
            prices = sorted(orderBook.buy_orders.keys(), reverse=True)
            VolumeTraded = 0
            i = 0
            while VolumeTraded < volume and i < len(prices):
                if priceLimit and prices[i] < priceLimit: break
                quantity = -orderBook.buy_orders[prices[i]]
                volOrdered = quantity
                if printTime: print("volOrdered + VolumeTraded > volume", volOrdered + VolumeTraded > volume)
                if (volOrdered + VolumeTraded > volume): 
                    volOrdered = volume - VolumeTraded
                    TradeFill = False
                    if printTime: print("volOrdered = volume - VolumeTraded:", volOrdered)
                print("SELLING", product, str(-volOrdered) + "x", prices[i])
                ordersMade.append(Order(product, prices[i], -volOrdered))
                VolumeTraded += volOrdered
                PriceTraded = prices[i]
                i += 1
            if not(TradeFill): nextBest = PriceTraded
            elif i < len(prices): nextBest = prices[i]
            else: nextBest = None
            return ordersMade, (PriceTraded, -VolumeTraded, TradeFill, nextBest)

    
    def PriceOrder(self, product, buy : int, state : TradingState, price : int, volumeLimit = 0, printTime = False):
        """Trades best prices until price hit (inclusive), optional max volume traded
        Returns a list of orders made and a tuple of last price traded at, total volume traded, 
        and if it filled the final order it traded at"""
        volumeLimit = abs(volumeLimit)
        ordersMade = []
        orderBook = state.order_depths[product]
        TradeFill = True
        PriceTraded = 0
        VolumeTraded = 0
        if buy:
            prices = sorted(orderBook.sell_orders.keys(), reverse=False)
            for listing in prices:
                if listing > price: break
                volOrdered = abs(orderBook.sell_orders[listing])
                if printTime: 
                    ans = volumeLimit != 0
                    if ans:
                        ans = str(ans) + ": " + str(volumeLimit)
                    print("volumeLimit:", ans)
                if volumeLimit:
                    if printTime: 
                        print("volOrdered:", volOrdered)
                        print("VolumeTraded + volOrdered > volumeLimit:", VolumeTraded + volOrdered > volumeLimit)
                    if VolumeTraded + volOrdered > volumeLimit:
                        volOrdered = volumeLimit - VolumeTraded
                        if printTime: print("volOrdered = volumeLimit - VolumeTraded:", volOrdered)
                        TradeFill = False
                        
                print("BUYING", product, str(volOrdered) + "x", listing)
                ordersMade.append(Order(product, listing, volOrdered))
                VolumeTraded += volOrdered
                PriceTraded = listing
            if not(TradeFill): nextBest = PriceTraded
            elif listing != PriceTraded: nextBest = listing
            else: nextBest = None
            if printTime and VolumeTraded:
                print("Price Traded:", PriceTraded)
                print("Volume Traded:", VolumeTraded)
                print("Trade Fill:", TradeFill)
                print("Next Best:", nextBest)
            return ordersMade, (PriceTraded, VolumeTraded, TradeFill, nextBest)
        else:
            prices = sorted(orderBook.buy_orders.keys(), reverse=True)
            for listing in prices:
                if listing < price: break
                volOrdered = orderBook.buy_orders[listing]
                if printTime: 
                    ans = volumeLimit != 0
                    if ans:
                        ans = str(ans) + ": " + str(volumeLimit)
                    print("volumeLimit:", ans)
                if volumeLimit:
                    if printTime: 
                        print("volOrdered:", volOrdered)
                        print("VolumeTraded + volOrdered > volumeLimit:", VolumeTraded + volOrdered > volumeLimit)
                    if VolumeTraded + volOrdered > volumeLimit:
                        volOrdered = volumeLimit - VolumeTraded
                        if printTime: print("volOrdered = volumeLimit - VolumeTraded:", volOrdered)
                        TradeFill = False
                print("SELLING", product, str(-volOrdered) + "x", listing)
                ordersMade.append(Order(product, listing, -volOrdered))
                VolumeTraded += volOrdered
                PriceTraded = listing
            if not(TradeFill): nextBest = PriceTraded
            elif listing != PriceTraded: nextBest = listing
            else: nextBest = None
            if printTime and VolumeTraded:
                print("Price Traded:", PriceTraded)
                print("Volume Traded:", -VolumeTraded)
                print("Trade Fill:", TradeFill)
                print("Next Best:", nextBest)
            return ordersMade, (PriceTraded, -VolumeTraded, TradeFill, nextBest)

    
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
