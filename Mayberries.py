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
    maxQuantities: Dict[Product, int] = {
        "BANANAS": 20,
        "PEARLS": 20,
        "PINA_COLADAS": 300,
        "COCONUTS": 600,
        "DIVING_GEAR": 50,
        "BERRIES": 250,
    }

    trackingStatsOf = ["BANANAS", "PEARLS", "PINA_COLADAS", "COCONUTS", "DIVING_GEAR", "BERRIES", "DOLPHIN_SIGHTINGS"]
    
    shortMovingAverages: Dict[Product, List[float]] = {    }

    longMovingAverages: Dict[Product, List[float]] = {    }

    ultraLongMovingAverages: Dict[Product, List[float]] = {    }

    shortVelocities: Dict[Product, List[float]] = {    }

    longVelocities: Dict[Product, List[float]] = {    }

    ultraLongVelocities: Dict[Product, List[float]] = {    }

    shortAccelerations: Dict[Product, float] = {    }

    longAccelerations: Dict[Product, float] = {    }

    ultraLongAccelerations: Dict[Product, float] = {    }
    

    shortTermAboveLongTerm: bool = False
    tryToBuy: bool = True
    daysSinceCross: int = 0

    basePinaColadaPrice: int = 0
    minPinaColadaRatioDifference: float = 0.00030
    pinaColadaRatioWeight: float = 0.05

    baseCoconutPrice: int = 0
    coconutsPriceMovingAverage: List[float] = []
    coconutsPriceMovingAverageLong: List[float] = []
    coconutsCrossedUp: bool = False

    done_initializing: bool = False # we use this to detect state resets

    # CONFIGURABLE PARAMETERS
    shortMovingAverageSize: int = 10
    longMovingAverageSize: int = 40
    ultraLongMovingAverageSize: int = 200
    stddevThreshold: float = 0.5
    exponentialSmoothing: float = 2.0
    # Define a fair value for the PEARLS.
    pearl_acceptable_price = 10000
    # ignored for now
    bananasQuantityAffinity: int = 2


    def __init__(self):
        # initialize the tracked stats
        for product in self.trackingStatsOf:
            self.shortMovingAverages[product] = []
            self.longMovingAverages[product] = []
            self.ultraLongMovingAverages[product] = []
            self.shortVelocities[product] = []
            self.longVelocities[product] = []
            self.ultraLongVelocities[product] = []
            self.shortAccelerations[product] = 0
            self.longAccelerations[product] = 0
            self.ultraLongAccelerations[product] = 0

    """
    Only method required. It takes all buy and sell orders for all symbols as an input,
    and outputs a list of orders to be sent
    """
    def run(self, state: TradingState) -> Dict[str, List[Order]]:
        if not self.done_initializing:
            if state.timestamp > 0:
                print("STATE MAY HAVE BEEN RESET")
            print("OPERATING WITH SMASIZE ", self.shortMovingAverageSize, "LONGSMASIZE", self.longMovingAverageSize, "STDDEVTHRESHOLD", self.stddevThreshold)
            print("TIMESTAMP, PRODUCT, POSITION, BID, PRICE, ASK, PRICE_EMA, LONGPRICE_EMA, STDDEV, DAYSSINCECROSS, TRYTOBUY, CSVDATA")
            self.done_initializing = True

        if self.getEffectivePrice(state.order_depths['PINA_COLADAS']) != -1 and self.basePinaColadaPrice == 0:
            self.basePinaColadaPrice = self.getEffectivePrice(state.order_depths['PINA_COLADAS'])

        if self.getEffectivePrice(state.order_depths['COCONUTS']) != -1 and self.baseCoconutPrice == 0:
            self.baseCoconutPrice = self.getEffectivePrice(state.order_depths['COCONUTS'])

        

        # Initialize the method output dict as an empty dict
        result = {}

        # Process the moving averages first
        for product in state.order_depths.keys():
            effectivePrice = self.getEffectivePrice(state.order_depths[product])
            self.processMovingAverage(product, self.shortMovingAverageSize, effectivePrice, False)
            self.processMovingAverage(product, self.longMovingAverageSize, effectivePrice, False)
            self.processMovingAverage(product, self.ultraLongMovingAverageSize, effectivePrice, False)
        # Handle buying and selling of each product
        for product in state.order_depths.keys():

            currentProductAmount = 0            
            try:
                currentProductAmount = state.position[product]
            except:
                pass
            
            # if product == "BANANAS":
            #     result[product] = self.handleBananas(state, product, currentProductAmount)
                
            # if product == 'PEARLS':
            #     result[product] = self.handlePearls(state, product, currentProductAmount)
                
            # if product == 'PINA_COLADAS':
            #     result[product] = self.handlePinaColadas(state, product, currentProductAmount)

            if product == 'COCONUTS':
                result[product] = self.handleCoconuts(state, product, currentProductAmount)
                self.writeLog(state, product)
                pass

            # if product == 'DIVING_GEAR':
            #     # result[product] = self.handleDivingGear(state, product, currentProductAmount)
            #     self.writeLog(state, product)
            #     pass

            # if product == 'MAYBERRIES':
            #     # result[product] = self.handleMayberries(state, product, currentProductAmount)
            #     self.writeLog(state, product)
            #     pass

        return result
    

    def handleCoconuts(self, state: TradingState, product: str, currentProductAmount: int) -> list[Order]:
        if len(self.shortMovingAverages[product]) < self.shortMovingAverageSize:
            return []
        
        order_depth = state.order_depths[product]
        velocity = self.shortVelocities[product][-1]
        accel = self.shortAccelerations[product]
        previousVelocity = 0.0 if len(self.shortVelocities[product]) < 2 else self.shortVelocities[product][-2]

        effectivePrice = self.getEffectivePrice(order_depth)
        orders: list[Order] = []

        priceAverage: float = Trader.computeSimpleAverage(self, self.shortMovingAverages[product])
        priceLongAverage: float = Trader.computeSimpleAverage(self, self.longMovingAverages[product])
        
        
        recentStandardDeviation: float = 0
        for observation in self.shortMovingAverages[product]:
            recentStandardDeviation += (observation - priceAverage) ** 2

        recentStandardDeviation = (recentStandardDeviation / len(self.shortMovingAverages[product])) ** 0.5

        self.writeLog(state, product, velocity, previousVelocity, self.coconutsCrossedUp)

        if len(self.shortVelocities[product]) < self.shortMovingAverageSize / 2:
            return orders

        try: 
            if self.shouldSell: self.shouldSell -= 1
        except: self.shouldSell = 0
        try:
            if self.shouldBuy: self.shouldBuy -= 1
        except: self.shouldBuy = 0
        
  
        if velocity < 0 and previousVelocity > 0 or velocity > 0 and previousVelocity < 0:
            if accel < 0: 
                self.shouldSell = 4
                self.shouldBuy = 0
            else: 
                self.shouldBuy = 4
                self.shouldSell = 0
        else:
            print("COCOUNUTS: velocity: ", velocity, " previousVelocity: ", previousVelocity, " at time ", state.timestamp, " so not changing cross")

        if len(order_depth.sell_orders) > 0 and self.shouldBuy: # we are going to consider buying
            print("AT TIME ", state.timestamp, "PRODUCT ", product, " HAS SELL ORDERS: ", state.order_depths[product].sell_orders)
            acceptable_buy_price = priceAverage + 5

            orders = orders + self.getAllOrdersBetterThan(product, state, True, acceptable_buy_price, currentProductAmount)

        if len(order_depth.buy_orders) > 0 and self.shouldSell: # we are going to consider selling
            print("AT TIME ", state.timestamp, "PRODUCT ", product, " HAS BUY ORDERS: ", state.order_depths[product].buy_orders)
            acceptable_sell_price = priceAverage - 5

            orders = orders + self.getAllOrdersBetterThan(product, state, False, acceptable_sell_price, currentProductAmount)
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

    def getAllOrdersBetterThan(self, product: str, state: TradingState, isBuying: bool, price: int, currentProductAmount: int) -> list[Order]:
        orders: list[Order] = []
        order_depth: OrderDepth = state.order_depths[product]
        maxAmount: int = Trader.maxQuantities[product]

        if isBuying:
            print("Looking to buy " + product + " at time " + str(state.timestamp) + " with price better than " + str(price) + " and orders: " + str(order_depth.sell_orders))
            for orderPrice in sorted(order_depth.sell_orders.keys(), reverse=True):
                if orderPrice <= price:
                    possibleQuantity: int = -1 * order_depth.sell_orders[orderPrice]
                    possibleQuantity = Trader.capVolume(currentProductAmount, possibleQuantity, maxAmount)
                    if possibleQuantity != 0:
                        orders.append(Order(product, orderPrice, possibleQuantity))
                        print("BUYING" + product + "AT TIME" + str(state.timestamp) + "WITH PRICE" + str(orderPrice) + "AND QUANTITY" + str(possibleQuantity))
        else: # selling
            print("Looking to sell " + product + " at time " + str(state.timestamp) + " with price better than " + str(price) + " and orders: " + str(order_depth.buy_orders))
            for orderPrice in sorted(order_depth.buy_orders.keys(), reverse=False):
                if orderPrice >= price:
                    possibleQuantity: int = -1 * order_depth.buy_orders[orderPrice]
                    possibleQuantity = Trader.capVolume(currentProductAmount, possibleQuantity, -1 * maxAmount)
                    if possibleQuantity != 0:
                        orders.append(Order(product, orderPrice, possibleQuantity))
                        print("SELLING" + product + "AT TIME" + str(state.timestamp) + "WITH PRICE" + str(orderPrice) + "AND QUANTITY" + str(possibleQuantity))
        
        return orders
    
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

    def processMovingAverage(self, product: str, movingAverageLength: int, nextValue: float, isSimple: bool = False):
        
        if movingAverageLength == self.shortMovingAverageSize:
            movingAverage = self.shortMovingAverages[product]
            movingVelocity = self.shortVelocities[product]
        elif movingAverageLength == self.longMovingAverageSize:
            movingAverage = self.longMovingAverages[product]
            movingVelocity = self.longVelocities[product]
        else:
            movingAverage = self.ultraLongMovingAverages[product]
            movingVelocity = self.ultraLongVelocities[product]



        if len(movingAverage) < 5 or isSimple:  # append the simple moving average
            movingAverage.append(nextValue)
        else: # append the exponential moving average
            movingAverage.append(
                nextValue * (self.exponentialSmoothing / (1 + movingAverageLength)) +
                movingAverage[-1] * (1 - (self.exponentialSmoothing / (1 + movingAverageLength))))

        if len(movingAverage) > movingAverageLength:
            movingAverage.pop(0)

        if len(movingAverage) > 1:
            nextVelocity = movingAverage[-1] - movingAverage[-2]
            if len(movingVelocity) < 1:
                movingVelocity.append(0)
            elif isSimple:
                movingVelocity.append(nextVelocity)
            else:
                movingVelocity.append(
                    nextVelocity * (self.exponentialSmoothing / (1 + movingAverageLength)) +
                    movingVelocity[-1] * (1 - (self.exponentialSmoothing / (1 + movingAverageLength))))
                
            if len(movingVelocity) > movingAverageLength:
                movingVelocity.pop(0)

        if len(movingVelocity) < movingAverageLength:
            return

        if movingAverageLength == self.shortMovingAverageSize:
            self.shortAccelerations[product] = (movingVelocity[-1] - movingVelocity[0]) / len(movingVelocity)
        elif movingAverageLength == self.longMovingAverageSize:
            self.longAccelerations[product] = (movingVelocity[-1] - movingVelocity[-2])
        else:
            self.ultraLongAccelerations[product] = (movingVelocity[-1] - movingVelocity[-2])

        

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


    def writeLog(self, state: TradingState, product: str, c1 = 0, c2 = 0, c3 = 0, c4 = 0, c5 = 0, c6 = 0):
        currentProductAmount = state.position.get(product, 0)
        bid = Trader.getBestPossiblePrice(self, state.order_depths[product], True)
        effectivePrice = Trader.getEffectivePrice(self, state.order_depths[product])
        ask = Trader.getBestPossiblePrice(self, state.order_depths[product], False)

        shortMa = self.computeSimpleAverage(self.shortMovingAverages[product])
        longMa = self.longMovingAverages[product][-1]
        ultraLongMa = self.ultraLongMovingAverages[product][-1]

        shortVel = 0 if len(self.shortVelocities) == 0 else self.shortVelocities[product][-1]
        longVel = 0 if len(self.longVelocities) == 0 else self.longVelocities[product][-1]
        ultraLongVel = 0 if len(self.ultraLongVelocities) == 0 else self.ultraLongVelocities[product][-1]

        shortAcc = self.shortAccelerations[product]
        longAcc = self.longAccelerations[product]
        ultraLongAcc = self.ultraLongAccelerations[product]

        print(state.timestamp, '"' + product + '"', currentProductAmount, bid, effectivePrice, ask, 
              shortMa, longMa, ultraLongMa, shortVel, longVel, ultraLongVel, shortAcc, longAcc, ultraLongAcc,
              
              c1,c2,c3,c4,c5,c6, '"CSVDATA"', sep=",")

######### UTILITY FUNCTIONS #########

    '''
    Static method to cap the volume of an order to avoid exceeding the cap
    -7, -4, -10 -> -3
    '''
    def capVolume(current: int, delta: int, cap: int) -> int:
        if abs(current + delta) > abs(cap):
            return cap - current
        return delta
    
    def weightedAverage(x1, x2, distance):
        return x1 + (x2 - x1) * distance
    
    def clamp(n, minn, maxn):
        return max(min(maxn, n), minn)