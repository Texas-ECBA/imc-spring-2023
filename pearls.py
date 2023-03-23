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

       
            if product == 'PEARLS':
                minpos = maxpos = currentProductAmount
                
                print("AT TIME ", state.timestamp, "PRODUCT ", product, " HAS POSITION: ", currentProductAmount)

                if len(order_depth.sell_orders) > 0:

                    print("AT TIME ", state.timestamp, "PRODUCT ", product, " HAS SELL ORDERS: ", state.order_depths[product].sell_orders)
                    if currentProductAmount != 20:
                        BuyOrders = self.PriceOrder(product, BUY, state, 10000, 20 - maxpos)
                        for x in BuyOrders[0]:
                            orders.append(x)
                        currentProductAmount += BuyOrders[1][1]
                        maxpos += BuyOrders[1][1]
                        BestSell = BuyOrders[1][3]
                    else:
                        BestSell = sorted(order_depth.sell_orders.keys(), reverse=False) [-1]


                if len(order_depth.buy_orders) != 0:

                    print("AT TIME ", state.timestamp, "PRODUCT ", product, " HAS BUY ORDERS: ", state.order_depths[product].buy_orders)
                    if currentProductAmount != -20:
                        SellOrders = self.PriceOrder(product, SELL, state, 10000, -20 - minpos, printTime = currentProductAmount < -15)
                        for x in SellOrders[0]:
                            orders.append(x)
                        currentProductAmount += SellOrders[1][1]
                        minpos += SellOrders[1][1]
                        BestBuy = SellOrders[1][3]
                    else:
                        BestBuy = sorted(order_depth.buy_orders.keys(), reverse=True) [-1]

                if type(BestBuy) == type(None):
                    BestBuy = 9995
                if type(BestSell) == type(None):
                    BestSell = 10005
                print("Current Pearl Market is", BestBuy, "-", BestSell)
                if BestBuy < 9999 or BestBuy < 10000 and currentProductAmount > 0:
                    BestBuy += 1
                    if maxpos < 20:
                        orders.append(Order(product, BestBuy, 20-maxpos))
                        if True: print("Placed Buy order of", 20-maxpos, product, "for", BestBuy)
                if BestSell > 10001 or BestSell > 10000 and currentProductAmount < 0:
                    BestSell -= 1
                    if minpos > -20:
                        orders.append(Order(product, BestSell, -20-minpos))
                        if True: print("Placed Sell order of", -20-minpos, product, "for", BestSell)        
                print("Pushed Pearl Market to", BestBuy, "-", BestSell)

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
        numOrders = 0
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
                numOrders += 1
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
            return ordersMade, (PriceTraded, VolumeTraded, TradeFill, nextBest), numOrders
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
                numOrders += 1
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
            return ordersMade, (PriceTraded, -VolumeTraded, TradeFill, nextBest), numOrders

    
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
