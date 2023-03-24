from typing import Dict, List
import math
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
    
    bananasPriceMovingAverage: List[float] = []
    bananasPriceMovingAverageLong: List[float] = []
    shortTermAboveLongTerm: bool = False
    tryToBuy: bool = True
    daysSinceCross: int = 0

    pearlsPriceMovingAverage: List[float] = []
    pearlsVelocityMovingAverage: List[float] = []

    basePinaColadaPrice: int = 0
    maxPinaColadaQuantity: int = 600

    baseCoconutPrice: int = 0
    maxCoconutQuantity: int = 300


    done_initializing: bool = False # we use this to detect state resets

    # CONFIGURABLE PARAMETERS
    movingAverageSize: int = 10
    longMovingAverageSize: int = 40
    stddevThreshold: float = 0.5
    exponentialSmoothing: float = 2.0
    # Define a fair value for the PEARLS.
    pearl_acceptable_price = 10000
    # ignored for now
    bananasQuantityAffinity: int = 2

    """
    Only method required. It takes all buy and sell orders for all symbols as an input,
    and outputs a list of orders to be sent
    """
    def run(self, state: TradingState) -> Dict[str, List[Order]]:
        if not self.done_initializing:
            print("OPERATING WITH SMASIZE ", self.movingAverageSize, "LONGSMASIZE", self.longMovingAverageSize, "STDDEVTHRESHOLD", self.stddevThreshold)
            print("TIMESTAMP, PRODUCT, POSITION, BID, PRICE, ASK, PRICE_EMA, LONGPRICE_EMA, STDDEV, DAYSSINCECROSS, TRYTOBUY, CSVDATA")
            self.done_initializing = True

        if self.getEffectivePrice(state.order_depths['PINA_COLADAS']) != -1 and self.basePinaColadaPrice == 0:
            self.basePinaColadaPrice = self.getEffectivePrice(state.order_depths['PINA_COLADAS'])

        if self.getEffectivePrice(state.order_depths['COCONUTS']) != -1 and self.baseCoconutPrice == 0:
            self.baseCoconutPrice = self.getEffectivePrice(state.order_depths['COCONUTS'])

        if not self.done_initializing and state.timestamp > 0:
            print("STATE MAY HAVE BEEN RESET")

        # Initialize the method output dict as an empty dict
        result = {}

        # Iterate over all the keys (the available products) contained in the order depths
        for product in state.order_depths.keys():

            currentProductAmount = 0            
            try:
                currentProductAmount = state.position[product]
            except:
                pass

            if product == "BANANAS":
                result[product] = self.handleBananas(state, product, currentProductAmount)
                
            if product == 'PEARLS':
                result[product] = self.handlePearls(state, product, currentProductAmount)
                
            if product == 'PINA_COLADAS':
                result[product] = self.handlePinaColadas(state, product, currentProductAmount)

            # if product == 'COCONUTS':
            #     result[product] = self.handleBananas(state, product, currentProductAmount)

        return result
    

    def handlePearls(self, state: TradingState, product: str, currentProductAmount: int) -> list[Order]:
        minpos = maxpos = currentProductAmount
                
        print("AT TIME ", state.timestamp, "PRODUCT ", product, " HAS POSITION: ", currentProductAmount)
        orders: list[Order] = []
        order_depth = state.order_depths[product]
        if len(order_depth.sell_orders) > 0:

            print("AT TIME ", state.timestamp, "PRODUCT ", product, " HAS SELL ORDERS: ", state.order_depths[product].sell_orders)
            if currentProductAmount != 20:
                BuyOrders = self.PriceOrder(product, BUY, state, 10000, 20 - maxpos)
                for x in BuyOrders[0]:
                    orders.append(x)
                    pass
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
                    pass
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
        return orders


    # def handleBananas(self, state: TradingState, product: str, currentProductAmount: int) -> list[Order]:
    #     minpos = maxpos = currentProductAmount
    #     try: market = state.market_trades[product]
    #     except: market = []
    #     prevprices = []
    #     for trade in market:
    #         prevprices.append(trade.price)
    #     prevprices = sorted(prevprices)

    #     print("AT TIME ", state.timestamp, "PRODUCT ", product, " HAS POSITION: ", currentProductAmount)
    #     orders: list[Order] = []
    #     order_depth = state.order_depths[product]
    #     BestSell = self.PriceOrder(product, BUY, state, 0)[1][3]
    #     BestBuy = self.PriceOrder(product, SELL, state, 0)[1][3]

    #     if type(BestBuy) == type(None):
    #         BestBuy = prevprices[0]
    #     if type(BestSell) == type(None):
    #         BestSell = prevprices[-1]
    #     print("Current Banana Market is", BestBuy, "-", BestSell)
    #     BestBuy += .1
    #     if maxpos < 20:
    #         orders.append(Order(product, BestBuy, 20-maxpos))
    #         print("Placed Buy order of", 20-maxpos, product, "for", BestBuy)
    #     BestSell -= 1
    #     if minpos > -20:
    #         orders.append(Order(product, BestSell, -20-minpos))
    #         print("Placed Sell order of", -20-minpos, product, "for", BestSell)        
    #     print("Pushed Banana Market to", BestBuy, "-", BestSell)
    #     return orders    
    
    
    def handleBananas(self, state: TradingState, product: str, currentProductAmount: int) -> list[Order]:
        orders: list[Order] = []
        order_depth = state.order_depths[product]
        effectivePrice = Trader.getEffectivePrice(self, order_depth)
        priceAverage: float = Trader.processMovingAverage(self, self.bananasPriceMovingAverage, self.movingAverageSize, effectivePrice, isSimple = True)
        priceLongAverage: float = Trader.processMovingAverage(self, self.bananasPriceMovingAverageLong, self.longMovingAverageSize, effectivePrice, isSimple = True)
        
        if (priceAverage == -1 or priceLongAverage == -1 or len(self.bananasPriceMovingAverageLong) < self.longMovingAverageSize):
            print("Not enough data to calculate moving average for bananas, skipping")
            return orders    
    
        isShortAboveLong = priceAverage > priceLongAverage

        if isShortAboveLong and not self.shortTermAboveLongTerm: # before it was below, now it's above
            # this is known as the golden cross, and it's a good time to buy
            print("GOLDEN CROSS AT TIME ", state.timestamp, "PRODUCT ", product, " HAS POSITION: ", currentProductAmount)
            self.tryToBuy = True
            self.daysSinceCross = 0
        elif not isShortAboveLong and self.shortTermAboveLongTerm: # before it was above, now it's below
            # this is known as the dead cross, and it's a good time to sell
            print("DEAD CROSS AT TIME ", state.timestamp, "PRODUCT ", product, " HAS POSITION: ", currentProductAmount)
            self.tryToBuy = False
            self.daysSinceCross = 0

        self.shortTermAboveLongTerm = isShortAboveLong
        self.daysSinceCross += 1

        recentStandardDeviation: float = 0
        for observation in self.bananasPriceMovingAverage:
            recentStandardDeviation += (observation - priceAverage) ** 2

        recentStandardDeviation = (recentStandardDeviation / len(self.bananasPriceMovingAverage)) ** 0.5

        self.writeLog(state, product, priceAverage, priceLongAverage, recentStandardDeviation, self.daysSinceCross, self.tryToBuy)

        if len(order_depth.sell_orders) > 0: # we are going to consider buying
            print("AT TIME ", state.timestamp, "PRODUCT ", product, " HAS SELL ORDERS: ", state.order_depths[product].sell_orders)
            possiblePrices = sorted(order_depth.sell_orders.keys(), reverse=True)

            acceptable_buy_price = priceAverage - recentStandardDeviation * self.stddevThreshold
            for price in possiblePrices:
                if price < acceptable_buy_price:
                    possibleQuantity: int = -1 * order_depth.sell_orders[price] # becomes some positive number
                    if possibleQuantity + currentProductAmount > self.maxPositionQuantity:
                        print("CANNOT BUY", product, str(possibleQuantity) + "x", price, "WHEN SMA IS", priceAverage, "AND STDDEV IS", recentStandardDeviation)
                        possibleQuantity = self.maxPositionQuantity - currentProductAmount

                    if possibleQuantity > 0:
                        if len(orders) > 0 and orders[-1].price == price:
                            orders[-1].quantity += possibleQuantity
                        else:
                            orders.append(Order(product, price, possibleQuantity))
                        # currentProductAmount += possibleQuantity
                        print("TRYING TO BUY", product, str(possibleQuantity) + "x", price, "WHEN SMA IS", priceAverage, "AND STDDEV IS", recentStandardDeviation)
                        

        if len(order_depth.buy_orders) > 0: # we are going to consider selling
            print("AT TIME ", state.timestamp, "PRODUCT ", product, " HAS BUY ORDERS: ", state.order_depths[product].buy_orders)
            possiblePrices = sorted(order_depth.buy_orders.keys())
            acceptable_sell_price = priceAverage + recentStandardDeviation * self.stddevThreshold
            for price in possiblePrices:
                if price > acceptable_sell_price:
                    possibleQuantity: int = -1 * order_depth.buy_orders[price] # becomes some negative number
                    if possibleQuantity + currentProductAmount < -1 * self.maxPositionQuantity:
                        possibleQuantity = -1 * self.maxPositionQuantity - currentProductAmount
                        print("CANNOT SELL", product, str(possibleQuantity) + "x", price, "WHEN SMA IS", priceAverage, "AND STDDEV IS", recentStandardDeviation)
                    if possibleQuantity < 0:                        
                        if len(orders) > 0 and orders[-1].price == price:
                            orders[-1].quantity += possibleQuantity
                        else:
                            orders.append(Order(product, price, possibleQuantity))

                        # currentProductAmount += possibleQuantity
                        print("TRYING TO SELL", product, str(possibleQuantity) + "x", price, "WHEN SMA IS", priceAverage, "AND STDDEV IS", recentStandardDeviation)

        return orders

    def handlePinaColadas(self, state: TradingState, product: str, currentProductAmount: int) -> List[Order]:
        
        order_depth = state.order_depths[product]
        #get effective price
        effectivePrice = self.getEffectivePrice(order_depth)
        orders: list[Order] = []

        if (effectivePrice == -1 or self.basePinaColadaPrice == 0 or self.baseCoconutPrice == 0):
            print("NOT READY TO TRADE PINA COLADAS AT TIME", state.timestamp)
            return orders
        
        normalizedPrice = effectivePrice / self.basePinaColadaPrice
        normalizedCocunutPrice = self.getEffectivePrice(state.order_depths["COCONUTS"]) / self.baseCoconutPrice
        
        self.writeLog(state, product, normalizedPrice, normalizedCocunutPrice)

        if normalizedPrice > normalizedCocunutPrice:
            # sell pina coladas, matching all open buy orders greater than the effective price - 1
            for price in sorted(order_depth.buy_orders.keys()):
                if price >= effectivePrice - 2:
                    desiredQuantity = -1 * order_depth.buy_orders[price]
                    desiredQuantity = Trader.capVolume(currentProductAmount, desiredQuantity, Trader.maxPinaColadaQuantity)
                    orders.append(Order(product, price, desiredQuantity))
        else:
            # buy pina coladas, matching all open sell orders less than the effective price + 1
            for price in sorted(order_depth.sell_orders.keys(), reverse=True):
                if price <= effectivePrice + 2:
                    desiredQuantity = -1 * order_depth.sell_orders[price]
                    desiredQuantity = Trader.capVolume(currentProductAmount, desiredQuantity, -1 * Trader.maxPinaColadaQuantity)
                    orders.append(Order(product, price, desiredQuantity))

        return orders




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

    def processMovingAverage(self, movingAverage: List[float], movingAverageLength: int, nextValue: float, isSimple: bool = False) -> float:
        
        if len(movingAverage) < movingAverageLength or isSimple:  # append the simple moving average
            movingAverage.append(nextValue)
        else: # append the exponential moving average
            movingAverage.append(
                nextValue * (self.exponentialSmoothing / (1 + movingAverageLength)) +
                movingAverage[-1] * (1 - (self.exponentialSmoothing / (1 + movingAverageLength))))

        if len(movingAverage) > movingAverageLength:
            movingAverage.pop(0)

        if len(movingAverage) < movingAverageLength or isSimple:
            return Trader.computeSimpleAverage(self, movingAverage) # return the simple moving average
        else:
            return movingAverage[-1] # return the exponential moving average

    def computeSimpleAverage(self, list: List) -> float:
        if len(list) == 0:
            return -1
        return sum(list) / len(list)
    
    '''
    Get the average of the best possible prices
    '''
    def getEffectivePrice(self, order_depth: OrderDepth): 
        priceOne = Trader.getBestPossiblePrice(self, order_depth=order_depth, isBuying=True)
        priceTwo = Trader.getBestPossiblePrice(self, order_depth=order_depth, isBuying=False)
        avg: float = 0.0
        q = 0

        if priceOne != -1:
            avg += priceOne
            q += 1
        if priceTwo != -1:
            avg += priceTwo
            q += 1

        if q > 0:
            avg /= q

        if avg == 0:
            return -1.0
        
        return avg

    '''
    Static method to cap the volume of an order to avoid exceeding the cap
    -7, -4, -10 -> -3
    '''
    def capVolume(current: int, delta: int, cap: int) -> int:
        if abs(current + delta) > abs(cap):
            return cap - current
        return delta
    
    def writeLog(self, state: TradingState, product: str, c1 = 0, c2 = 0, c3 = 0, c4 = 0, c5 = 0):
        currentProductAmount = state.position.get(product, 0)
        bid = Trader.getBestPossiblePrice(self, state.order_depths[product], True)
        effectivePrice = Trader.getEffectivePrice(self, state.order_depths[product])
        ask = Trader.getBestPossiblePrice(self, state.order_depths[product], False)
        print(state.timestamp, '"' + product + '"', currentProductAmount, bid, effectivePrice, ask, c1,c2,c3,c4,c5, '"CSVDATA"', sep=",")
