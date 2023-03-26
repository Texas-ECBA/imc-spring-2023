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
    def __init__(self, symbol: Symbol, price: int, quantity: int, buyer: UserId = None, seller: UserId = None, timestamp: int = 0) -> None: # type: ignore
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

    basePinaColadaPrice: float = 0
    minPinaColadaRatioDifference: float = 0.0004
    pinaColadaRatioWeight: float = 0.05

    baseCoconutPrice: float = 0
    coconutsPriceMovingAverage: List[float] = []
    coconutsPriceMovingAverageLong: List[float] = []
    coconutsCrossedUp: bool = False
    coconutsDaysSinceCross: int = 0

    done_initializing: bool = False # we use this to detect state resets

    # CONFIGURABLE PARAMETERS
    shortMovingAverageSize: int = 10
    longMovingAverageSize: int = 50
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
            print("OPERATING WITH SMASIZE ", self.shortMovingAverageSize, "LONGSMASIZE", self.longMovingAverageSize, "ULTRALONGSMASIZE", self.ultraLongMovingAverageSize)
            self.done_initializing = True

        if self.getEffectivePrice(state.order_depths['PINA_COLADAS']) != -1 and self.basePinaColadaPrice == 0:
            self.basePinaColadaPrice = self.getEffectivePrice(state.order_depths['PINA_COLADAS'])

        if self.getEffectivePrice(state.order_depths['COCONUTS']) != -1 and self.baseCoconutPrice == 0:
            self.baseCoconutPrice = self.getEffectivePrice(state.order_depths['COCONUTS'])


        # Initialize the method output dict as an empty dict
        result = {}

        for product in state.observations:
            self.processMovingAverage(product, self.shortMovingAverageSize, state.observations[product], False)
            self.processMovingAverage(product, self.longMovingAverageSize, state.observations[product], False)
            self.processMovingAverage(product, self.ultraLongMovingAverageSize, state.observations[product], False)
            self.writeLog(state, product, is_observation=True)

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
            
            if product == "BANANAS":
                result[product] = self.handleBananasOLD(state, product, currentProductAmount)
                
            if product == 'PEARLS':
                result[product] = self.handlePearls(state, product, currentProductAmount)
                
            if product == 'PINA_COLADAS':
                result[product] = self.handlePinaColadas(state, product, currentProductAmount)

            if product == 'COCONUTS':
                result[product] = self.handleCoconuts(state, product, currentProductAmount)
                pass

            if product == 'DIVING_GEAR':
                result[product] = self.handleDivingGear(state, product, currentProductAmount)
                pass

            if product == 'BERRIES':
                #result[product] = self.handleBerriesTrends(state, product, currentProductAmount)
                result[product] = self.handleMayberries(state, product, currentProductAmount)
                pass

        return result
    
# --------------------- START PRODUCT HANDLERS --------------------- #

    def handlePearls(self, state: TradingState, product: str, currentProductAmount: int) -> list[Order]:
        minpos = maxpos = currentProductAmount
                
        #print("AT TIME ", state.timestamp, "PRODUCT ", product, " HAS POSITION: ", currentProductAmount)
        orders: list[Order] = []
        order_depth = state.order_depths[product]
        if len(order_depth.sell_orders) > 0:

            #print("AT TIME ", state.timestamp, "PRODUCT ", product, " HAS SELL ORDERS: ", state.order_depths[product].sell_orders)
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

            #print("AT TIME ", state.timestamp, "PRODUCT ", product, " HAS BUY ORDERS: ", state.order_depths[product].buy_orders)
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

        if type(BestBuy) == type(None): # type: ignore
            BestBuy = 9995
        if type(BestSell) == type(None): # type: ignore
            BestSell = 10005
        # print("Current Pearl Market is", BestBuy, "-", BestSell)
        if BestBuy < 9999 or BestBuy < 10000 and currentProductAmount > 0: # type: ignore
            BestBuy += 1 # type: ignore
            if maxpos < 20:
                orders.append(Order(product, BestBuy, 20-maxpos))
                #if True: print("Placed Buy order of", 20-maxpos, product, "for", BestBuy)
        if BestSell > 10001 or BestSell > 10000 and currentProductAmount < 0: # type: ignore
            BestSell -= 1 # type: ignore
            if minpos > -20:
                orders.append(Order(product, BestSell, -20-minpos))
                #if True: print("Placed Sell order of", -20-minpos, product, "for", BestSell)        
        # print("Pushed Pearl Market to", BestBuy, "-", BestSell)
        return orders
    
    def handleBananas(self, state:TradingState, product: str, currentProductAmount: int) -> list[Order]: 
        if len(self.shortMovingAverages[product]) < self.shortMovingAverageSize:
            return []
        
        order_depth = state.order_depths[product]
        shortVel = self.shortVelocities[product][-1]

        effectivePrice = self.getEffectivePrice(order_depth)
        orders: list[Order] = []

        priceAverage: float = self.shortMovingAverages[product][-1]
                
        recentStandardDeviation: float = 0
        for observation in self.shortMovingAverages[product]:
            recentStandardDeviation += (observation - priceAverage) ** 2

        recentStandardDeviation = (recentStandardDeviation / len(self.shortMovingAverages[product])) ** 0.5


        if len(self.shortVelocities[product]) < self.shortMovingAverageSize / 2:
            return orders

        
        shortMa = self.shortMovingAverages[product][-1]
        longMa = self.longMovingAverages[product][-1]
        ultraLongMa = self.ultraLongMovingAverages[product][-1]

        acceptable_buy_price = weightedAverage(priceAverage, effectivePrice, sigmoid(abs(2 * shortVel))) + abs(priceAverage - ultraLongMa) + 2 * abs(shortVel - 0.1)
        acceptable_sell_price = weightedAverage(priceAverage, effectivePrice, sigmoid(abs(2 * shortVel))) - abs(priceAverage - ultraLongMa) - 2 * abs(shortVel + 0.1)

        self.writeLog(state, product, acceptable_buy_price, acceptable_sell_price, getDiff(longMa, ultraLongMa))
        

        if len(order_depth.sell_orders) > 0 and effectivePrice > longMa and shortMa > longMa and (shortVel > 0.04 or significantDiff(longMa, ultraLongMa, 0.0002)):
            orders = orders + self.getAllOrdersBetterThan(product, state, True, acceptable_buy_price, currentProductAmount)

        if len(order_depth.buy_orders) > 0 and effectivePrice < longMa and shortMa < longMa and (shortVel < -0.04 or significantDiff(longMa, ultraLongMa, 0.0002)):
            orders = orders + self.getAllOrdersBetterThan(product, state, False, acceptable_sell_price, currentProductAmount)
        
        return orders

    def handleBananasOLD(self, state: TradingState, product: str, currentProductAmount: int) -> list[Order]:
        orders: list[Order] = []
        order_depth = state.order_depths[product]        
        priceAverage: float = Trader.computeSimpleAverage(self, self.shortMovingAverages[product])
        priceLongAverage: float = Trader.computeSimpleAverage(self, self.longMovingAverages[product])
        
        if (priceAverage == -1 or priceLongAverage == -1 or len(self.longMovingAverages[product]) < self.longMovingAverageSize):
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
        for observation in self.shortMovingAverages[product]:
            recentStandardDeviation += (observation - priceAverage) ** 2

        recentStandardDeviation = (recentStandardDeviation / len(self.shortMovingAverages[product])) ** 0.5

        self.writeLog(state, product, priceAverage, priceLongAverage, recentStandardDeviation)

        if len(order_depth.sell_orders) > 0: # we are going to consider buying
            print("AT TIME ", state.timestamp, "PRODUCT ", product, " HAS SELL ORDERS: ", state.order_depths[product].sell_orders)
            acceptable_buy_price = priceAverage - recentStandardDeviation * self.stddevThreshold

            orders = orders + self.getAllOrdersBetterThan(product, state, True, acceptable_buy_price, currentProductAmount)

        if len(order_depth.buy_orders) > 0: # we are going to consider selling
            print("AT TIME ", state.timestamp, "PRODUCT ", product, " HAS BUY ORDERS: ", state.order_depths[product].buy_orders)
            acceptable_sell_price = priceAverage + recentStandardDeviation * self.stddevThreshold

            orders = orders + self.getAllOrdersBetterThan(product, state, False, acceptable_sell_price, currentProductAmount)
        return orders

    def handlePinaColadas(self, state: TradingState, product: str, currentProductAmount: int) -> list[Order]:
        
        order_depth = state.order_depths[product]
        #get effective price
        effectivePrice = self.getEffectivePrice(order_depth)
        orders: list[Order] = []

        if (effectivePrice == -1 or self.basePinaColadaPrice == 0 or self.baseCoconutPrice == 0):
            print("NOT READY TO TRADE PINA COLADAS AT TIME", state.timestamp)
            return orders
        
        normalizedPrice = self.shortMovingAverages[product][-1] / self.basePinaColadaPrice
        normalizedCoconutPrice = self.shortMovingAverages["COCONUTS"][-1] / self.baseCoconutPrice
        
        ratio = normalizedPrice / normalizedCoconutPrice

        # this helps us avoid selling on long-term upswings and buying on long-term downswings until they turn around
        versusUltraLongVel = 0
        if len(self.ultraLongVelocities["COCONUTS"]) > 0:
            versusUltraLongVel = removeNoise(self.ultraLongVelocities["COCONUTS"][-1], 0.001)
        
        versusLongVel = 0
        if len(self.longVelocities["COCONUTS"]) > 0:
            versusLongVel = centeredSigmoid(removeNoise(self.longVelocities["COCONUTS"][-1], 0.1) * 7)

        versusUltraLongAcc = centeredSigmoid(removeNoise(self.ultraLongAccelerations["COCONUTS"], 0.00225) * 1000)

        ownLongVel = centeredSigmoid(removeNoise(self.longVelocities[product][-1], 0.4) * 8)
        ownLongAcc = centeredSigmoid(removeNoise(self.longAccelerations[product], 0.04) * 50)


        concavityFactor = centeredSigmoid((1 + ownLongAcc) * (1 + ownLongVel) - 1)
        if differentSigns(ownLongVel, ownLongAcc):
            concavityFactor = 0

        coconutConcavityFactor = centeredSigmoid((1 + versusUltraLongAcc) * (1 + versusLongVel) - 1)
        if differentSigns(versusLongVel, versusUltraLongAcc):
            coconutConcavityFactor = 0

        if state.timestamp < 2500:
            coconutConcavityFactor = 0
            concavityFactor = 0
            versusUltraLongVel *= state.timestamp / 2500 / 2
            versusUltraLongAcc *= state.timestamp / 2500 / 2

        base = clamp(1 + versusUltraLongVel / 40 + versusUltraLongAcc / 200 + versusLongVel / 200 + concavityFactor / 40 + coconutConcavityFactor / 80, 0.95, 1.05)

        desperation = max(0, 3.5 * math.tan(centeredSigmoid(removeNoise(abs(base - ratio), 0.001) * 1000) * math.pi / 2.5)) + 0.5


        
        closeDirection = 0 # 1 is buy to close, -1 is sell to close
        closeUrgency = 0
        if abs(ratio - base) < self.minPinaColadaRatioDifference: # if we're near the ratio, consider closing
            # try close position if our position is opposite the trend of coconuts
            if currentProductAmount > 0 and removeNoise(self.ultraLongVelocities["COCONUTS"][-1], 0.01) < 0: # sell
                closeUrgency += abs(removeNoise(self.ultraLongVelocities["COCONUTS"][-1], 0.01)) * 40
                closeDirection = -1
            elif currentProductAmount < 0 and removeNoise(self.ultraLongVelocities["COCONUTS"][-1], 0.01) > 0: # buy
                closeUrgency += abs(removeNoise(self.ultraLongVelocities["COCONUTS"][-1], 0.01)) * 40
                closeDirection = 1
        
        coconutPriceAverage = self.shortMovingAverages["COCONUTS"][-1]
        coconutLongMa = self.longMovingAverages["COCONUTS"][-1]
        coconutUltraLongMa = self.ultraLongMovingAverages["COCONUTS"][-1]
        
        coconutUltraLongTermTrend = getTrend(self.ultraLongMovingAverages["COCONUTS"],  self.ultraLongMovingAverageSize, 0.0002) + getTrend(self.ultraLongMovingAverages["COCONUTS"],  self.ultraLongMovingAverageSize, 0.0004)
        coconutLongTermTrend = getTrend(self.longMovingAverages["COCONUTS"],  self.longMovingAverageSize, 0.0001)

        totalTrend = -1 if (coconutUltraLongTermTrend + coconutLongTermTrend <= -2) else 1 if (coconutUltraLongTermTrend + coconutLongTermTrend >= 2) else 0
        
        # if we are short during a downward spike (or long during an upward spike), we should close our position
        if currentProductAmount < 0 and significantDiffDirectional(coconutPriceAverage, coconutLongMa, 0.0003) and significantDiffDirectional(coconutLongMa, coconutUltraLongMa, 0.0003) and totalTrend != -1:
            closeUrgency += abs(diffDirectional(coconutPriceAverage, coconutLongMa) - 0.0003) * 500 + abs(diffDirectional(coconutLongMa, coconutUltraLongMa) - 0.0003) * 500
            closeDirection = 1 # buy to close
        elif currentProductAmount > 0 and significantDiffDirectional(coconutPriceAverage, coconutLongMa, -0.0003) and significantDiffDirectional(coconutLongMa, coconutUltraLongMa, -0.0003) and totalTrend != 1:
            closeUrgency += abs(diffDirectional(coconutPriceAverage, coconutLongMa) + 0.0003) * 500 + abs(diffDirectional(coconutLongMa, coconutUltraLongMa) + 0.0003) * 500
            closeDirection = -1 # sell to close

        self.writeLog(state, product, normalizedPrice, normalizedCoconutPrice, ratio, base + self.minPinaColadaRatioDifference, base - self.minPinaColadaRatioDifference, totalTrend)


        if closeDirection != 0:
            if currentProductAmount > 0 and closeDirection == -1: # sell
                orders = self.getAllOrdersBetterThan(product, state, False, effectivePrice - desperation - closeUrgency, currentProductAmount, alt_max=0)
            elif currentProductAmount < 0 and closeDirection == 1: # buy
                orders = self.getAllOrdersBetterThan(product, state, True, effectivePrice + desperation + closeUrgency, currentProductAmount, alt_max=0)
            if len(orders) > 0:
                return orders

        if ratio > base + self.minPinaColadaRatioDifference:
            # sell pina coladas
            orders = self.getAllOrdersBetterThan(product, state, False, effectivePrice - desperation, currentProductAmount)
        if ratio < base - self.minPinaColadaRatioDifference:
            # buy pina coladas
            orders = self.getAllOrdersBetterThan(product, state, True, effectivePrice + desperation, currentProductAmount)
        
        return orders

    def handleCoconuts(self, state: TradingState, product: str, currentProductAmount: int) -> list[Order]:
        if len(self.shortMovingAverages[product]) < self.shortMovingAverageSize:
            return []
        
        order_depth = state.order_depths[product]
        shortVel = self.shortVelocities[product][-1]

        effectivePrice = self.getEffectivePrice(order_depth)
        orders: list[Order] = []

        priceAverage: float = self.shortMovingAverages[product][-1]
                
        recentStandardDeviation: float = 0
        for observation in self.shortMovingAverages[product]:
            recentStandardDeviation += (observation - priceAverage) ** 2

        recentStandardDeviation = (recentStandardDeviation / len(self.shortMovingAverages[product])) ** 0.5


        if len(self.shortVelocities[product]) < self.shortMovingAverageSize / 2:
            return orders

        shortMa = self.shortMovingAverages[product][-1]
        longMa = self.longMovingAverages[product][-1]
        ultraLongMa = self.ultraLongMovingAverages[product][-1]

        acceptable_buy_price = weightedAverage(priceAverage, effectivePrice, sigmoid(abs(2 * shortVel))) + abs(priceAverage - ultraLongMa) + 0.2 * abs(shortVel - 0.8)
        acceptable_sell_price = weightedAverage(priceAverage, effectivePrice, sigmoid(abs(2 * shortVel))) - abs(priceAverage - ultraLongMa) - 0.2 * abs(shortVel + 0.8)

        self.writeLog(state, product, acceptable_buy_price, acceptable_sell_price, getDiff(longMa, ultraLongMa))
        

        if len(order_depth.sell_orders) > 0 and shortMa > longMa and longMa > ultraLongMa and (shortVel > 0.06 or significantDiff(longMa, ultraLongMa, 0.0002)):
            orders = orders + self.getAllOrdersBetterThan(product, state, True, acceptable_buy_price, currentProductAmount)

        if len(order_depth.buy_orders) > 0 and shortMa < longMa and longMa < ultraLongMa and  (shortVel < -0.06 or significantDiff(longMa, ultraLongMa, 0.0002)):
            orders = orders + self.getAllOrdersBetterThan(product, state, False, acceptable_sell_price, currentProductAmount)
        
        return orders

    def handleMayberries(self, state: TradingState, product: str, currentProductAmount: int) -> list[Order]:
        if len(self.shortMovingAverages[product]) < self.shortMovingAverageSize:
            return []
        
        order_depth = state.order_depths[product]
        shortVel = self.shortVelocities[product][-1]

        effectivePrice = self.getEffectivePrice(order_depth)
        orders: list[Order] = []

        priceAverage: float = self.shortMovingAverages[product][-1]
                
        """
        recentStandardDeviation: float = 0
        for observation in self.shortMovingAverages[product]:
            recentStandardDeviation += (observation - priceAverage) ** 2

        recentStandardDeviation = (recentStandardDeviation / len(self.shortMovingAverages[product])) ** 0.5
        """

        """
        if len(self.shortVelocities[product]) < self.shortMovingAverageSize / 2:
            return orders
        
        
        shortMa = self.shortMovingAverages[product][-1]
        longMa = self.longMovingAverages[product][-1]
        ultraLongMa = self.ultraLongMovingAverages[product][-1]
        

        
        acceptable_buy_price = weightedAverage(priceAverage, effectivePrice, sigmoid(abs(3 * shortVel))) + 2 * abs(priceAverage - ultraLongMa) + 2 * abs(shortVel - 0.05) + 0.5
        acceptable_sell_price = weightedAverage(priceAverage, effectivePrice, sigmoid(abs(3 * shortVel))) - 2 * abs(priceAverage - ultraLongMa) - 2 * abs(shortVel + 0.05) - 0.5

        self.writeLog(state, product, acceptable_buy_price, acceptable_sell_price)
        
        


        if len(order_depth.sell_orders) > 0 and shortMa > longMa and longMa > ultraLongMa and (shortVel > 0.03 or significantDiff(longMa, ultraLongMa, 0.0002)):
            orders = orders + self.getAllOrdersBetterThan(product, state, True, acceptable_buy_price, currentProductAmount, force_if_empty=True)

        if len(order_depth.buy_orders) > 0 and shortMa < longMa and longMa < ultraLongMa and (shortVel < -0.03 or significantDiff(longMa, ultraLongMa, 0.0002)):
            orders = orders + self.getAllOrdersBetterThan(product, state, False, acceptable_sell_price, currentProductAmount, force_if_empty=True)

        """

        acceptable_buy_prices = Trader.getBestPossiblePrice(self, order_depth=order_depth, isBuying=True)
        acceptable_sell_prices = Trader.getBestPossiblePrice(self, order_depth=order_depth, isBuying=False)
        acceptable_buy_price = acceptable_buy_prices + 1
        acceptable_sell_price = acceptable_sell_prices - 1

        self.writeLog(state, product, acceptable_buy_price, acceptable_sell_price)

        if(acceptable_buy_price < (priceAverage - 2)):
            orders.append(Order(product,acceptable_buy_price, 25))

        if(acceptable_sell_price > (priceAverage + 2)):
            orders.append(Order(product,acceptable_sell_price, 25))

        orders = orders + self.handleBerriesTrends(state, product, currentProductAmount)
        return orders
    
    def handleBerriesTrends(self, state: TradingState, product: str, currentProductAmount: int) -> list[Order]:
        orders: list[Order] = []
        order_depth = state.order_depths[product]        
        priceAverage: float = Trader.computeSimpleAverage(self, self.shortMovingAverages[product])
        priceLongAverage: float = Trader.computeSimpleAverage(self, self.longMovingAverages[product])
        
        if (priceAverage == -1 or priceLongAverage == -1 or len(self.longMovingAverages[product]) < self.longMovingAverageSize):
            print("Not enough data to calculate moving average for berries, skipping")
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
        for observation in self.shortMovingAverages[product]:
            recentStandardDeviation += (observation - priceAverage) ** 2

        recentStandardDeviation = (recentStandardDeviation / len(self.shortMovingAverages[product])) ** 1

        self.writeLog(state, product, priceAverage, priceLongAverage, recentStandardDeviation)

        if len(order_depth.sell_orders) > 0: # we are going to consider buying
            print("AT TIME ", state.timestamp, "PRODUCT ", product, " HAS SELL ORDERS: ", state.order_depths[product].sell_orders)
            acceptable_buy_price = priceAverage - recentStandardDeviation * self.stddevThreshold

            orders = orders + self.getAllOrdersBetterThan(product, state, True, acceptable_buy_price, currentProductAmount)

        if len(order_depth.buy_orders) > 0: # we are going to consider selling
            print("AT TIME ", state.timestamp, "PRODUCT ", product, " HAS BUY ORDERS: ", state.order_depths[product].buy_orders)
            acceptable_sell_price = priceAverage + recentStandardDeviation * self.stddevThreshold

            orders = orders + self.getAllOrdersBetterThan(product, state, False, acceptable_sell_price, currentProductAmount)
        return orders


    def handleDivingGear(self, state: TradingState, product: str, currentProductAmount: int) -> list[Order]:
        if len(self.shortMovingAverages[product]) < self.shortMovingAverageSize:
            return []
        
        order_depth = state.order_depths[product]
        shortVel = self.shortVelocities[product][-1]

        effectivePrice = self.getEffectivePrice(order_depth)
        orders: list[Order] = []

        priceAverage: float = self.shortMovingAverages[product][-1]

        if len(self.shortVelocities[product]) < self.shortMovingAverageSize / 2:
            return orders
        
        shortMa = self.shortMovingAverages[product][-1]
        longMa = self.longMovingAverages[product][-1]
        ultraLongMa = self.ultraLongMovingAverages[product][-1]

        acceptable_buy_price = weightedAverage(priceAverage, effectivePrice, sigmoid(abs(3 * shortVel))) + 2 * abs(priceAverage - ultraLongMa) + 2 * abs(shortVel - 0.05) + 0.5
        acceptable_sell_price = weightedAverage(priceAverage, effectivePrice, sigmoid(abs(3 * shortVel))) - 2 * abs(priceAverage - ultraLongMa) - 2 * abs(shortVel + 0.05) - 0.5

        self.writeLog(state, product, acceptable_buy_price, acceptable_sell_price, getDiff(ultraLongMa, shortMa), significantDiff(priceAverage, ultraLongMa, 0.005))
        
        placedOrder = False

        # buying conditions
        if significantDiffDirectional(priceAverage, ultraLongMa, 0.0005):
            orders = orders + self.getAllOrdersBetterThan(product, state, True, acceptable_buy_price, currentProductAmount)
            placedOrder = True

        # selling conditions
        if significantDiffDirectional(priceAverage, ultraLongMa, -0.0005):
            orders = orders + self.getAllOrdersBetterThan(product, state, False, acceptable_sell_price, currentProductAmount)
            placedOrder = True

        if currentProductAmount > 0 and priceAverage > ultraLongMa and not placedOrder:
            # try to close out position to secure profit (sell)
            orders = orders + self.getAllOrdersBetterThan(product, state, False, acceptable_sell_price, currentProductAmount, alt_max=0)
        
        if currentProductAmount < 0 and priceAverage < ultraLongMa and not placedOrder:
            # try to close out position to secure profit (buy)
            orders = orders + self.getAllOrdersBetterThan(product, state, True, acceptable_buy_price, currentProductAmount, alt_max=0)
        
        return orders


# --------------------- END PRODUCT HANDLERS --------------------- #

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
        listing = None
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

    def getAllOrdersBetterThan(self, product: str, state: TradingState, isBuying: bool, price: float, currentProductAmount: int, alt_max: int = -9999, force_if_empty = False) -> list[Order]:
        orders: list[Order] = []
        order_depth: OrderDepth = state.order_depths[product]
        maxAmount: int = alt_max if alt_max != -9999 else Trader.maxQuantities[product]
        quantity_guaranteed_filled: int = 0

        if isBuying:
            print("Looking to buy " + product + " at time " + str(state.timestamp) + " with price better than " + str(price) + " and orders: " + str(order_depth.sell_orders))
            for orderPrice in sorted(order_depth.sell_orders.keys(), reverse=True):
                if orderPrice <= price:
                    possibleQuantity: int = -1 * order_depth.sell_orders[orderPrice]
                    possibleQuantity = capVolume(currentProductAmount, possibleQuantity, maxAmount)
                    if possibleQuantity != 0:
                        orders.append(Order(product, orderPrice, possibleQuantity))
                        quantity_guaranteed_filled += possibleQuantity
                        print("BUYING" + product + "AT TIME" + str(state.timestamp) + "WITH PRICE" + str(orderPrice) + "AND QUANTITY" + str(possibleQuantity))

            # if we placed no orders, then place a order at price
            if len(orders) == 0 and force_if_empty:
                orders.append(Order(product, math.ceil(price), maxAmount - currentProductAmount - quantity_guaranteed_filled))
        else: # selling
            print("Looking to sell " + product + " at time " + str(state.timestamp) + " with price better than " + str(price) + " and orders: " + str(order_depth.buy_orders))
            for orderPrice in sorted(order_depth.buy_orders.keys(), reverse=False):
                if orderPrice >= price:
                    possibleQuantity: int = -1 * order_depth.buy_orders[orderPrice]
                    possibleQuantity = capVolume(currentProductAmount, possibleQuantity, -1 * maxAmount)
                    if possibleQuantity != 0:
                        orders.append(Order(product, orderPrice, possibleQuantity))
                        quantity_guaranteed_filled += possibleQuantity
                        print("SELLING" + product + "AT TIME" + str(state.timestamp) + "WITH PRICE" + str(orderPrice) + "AND QUANTITY" + str(possibleQuantity))
            
            # if we placed no orders, then place a order at price
            if len(orders) == 0 and force_if_empty:
                orders.append(Order(product, math.floor(price), -1 * maxAmount - currentProductAmount - quantity_guaranteed_filled))

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

    # WARNING: changing this function will have many side effects !!!
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


        if len(movingAverage) < 1 or isSimple:  # append the simple moving average
            movingAverage.append(nextValue)
        else: # append the exponential moving average
            movingAverage.append(
                nextValue * (self.exponentialSmoothing / (1 + movingAverageLength)) +
                movingAverage[-1] * (1 - (self.exponentialSmoothing / (1 + movingAverageLength))))

        if len(movingAverage) > movingAverageLength:
            movingAverage.pop(0)

        if len(movingVelocity) < 1:
                movingVelocity.append(0)

        if len(movingAverage) > 1:
            nextVelocity = movingAverage[-1] - movingAverage[-2]
            if len(movingVelocity) < 1:
                movingVelocity.append(0)
            elif isSimple:
                movingVelocity.append(nextVelocity)
            else:
                movingVelocity.append(
                    nextVelocity * min(0.15, (10 * self.exponentialSmoothing / (1 + movingAverageLength))) +
                    movingVelocity[-1] * (1 - min(0.15, (10 * self.exponentialSmoothing / (1 + movingAverageLength)))))
                
            if len(movingVelocity) > movingAverageLength:
                movingVelocity.pop(0)

        if len(movingVelocity) < 5:
            return

        newAcceleration = movingVelocity[-1] - movingVelocity[-2]

        if movingAverageLength == self.shortMovingAverageSize:
            self.shortAccelerations[product] = newAcceleration * 0.3 + self.shortAccelerations[product] * 0.7
        elif movingAverageLength == self.longMovingAverageSize:
            self.longAccelerations[product] = newAcceleration * 0.3 + self.longAccelerations[product] * 0.7
        else:
            self.ultraLongAccelerations[product] = newAcceleration * 0.3 + self.ultraLongAccelerations[product] * 0.7

    def computeSimpleAverage(self, list: List) -> float:
        if len(list) == 0:
            return -1
        return sum(list) / len(list)
    
    '''
    Get the average of the best possible prices
    '''
    def getEffectivePrice(self, order_depth: OrderDepth) -> float: 
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


    def writeLog(self, state: TradingState, product: str, c1 = 0.0, c2 = 0.0, c3 = 0.0, c4 = 0.0, c5 = 0.0, c6 = 0.0, is_observation = False):
        currentProductAmount = state.position.get(product, 0)
        bid = Trader.getBestPossiblePrice(self, state.order_depths[product], True) if not is_observation else state.observations[product]
        effectivePrice = Trader.getEffectivePrice(self, state.order_depths[product]) if not is_observation else state.observations[product]
        ask = Trader.getBestPossiblePrice(self, state.order_depths[product], False) if not is_observation else state.observations[product]

        shortMa = self.shortMovingAverages[product][-1]
        longMa = self.longMovingAverages[product][-1]
        ultraLongMa = self.ultraLongMovingAverages[product][-1]

        shortVel = 0 if len(self.shortVelocities[product]) == 0 else self.shortVelocities[product][-1]
        longVel = 0 if len(self.longVelocities[product]) == 0 else self.longVelocities[product][-1]
        ultraLongVel = 0 if len(self.ultraLongVelocities[product]) == 0 else self.ultraLongVelocities[product][-1]

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

def weightedAverage(x1: float, x2: float, distance) -> float:
    return x1 + (x2 - x1) * distance

def clamp(n: float, minn: float, maxn: float) -> float:
    return max(min(maxn, n), minn)

def sigmoid(x) -> float:
    sig = 1 / (1 + math.exp(-x))
    return sig


'''
Returns a sigmoid centered at y = 0 instead of y = 0.5
'''
def centeredSigmoid(x: float) -> float:
    sig = 1 / (1 + math.exp(-x)) - 0.5
    return sig

def significantDiff(x1: float, x2: float, threshold: float) -> bool:
    x1 = abs(x1)
    x2 = abs(x2)
    return getDiff(x1, x2) > threshold

def getDiff(x1: float, x2: float) -> float:
    return abs(x1 - x2) / ((x1 + x2) / 2)

def removeNoise(x: float, threshold: float) -> float:
    if abs(x) < threshold:
        return 0
    
    # make x closer to 0 by the threshold
    if x > 0:
        return x - threshold
    else:
        return x + threshold
    

def significantDiffDirectional(x1: float, x2: float, threshold: float) -> bool:
    diff = (x2 - x1) / ((x1 + x2) / 2)
    return diff > threshold if threshold > 0 else diff < threshold

def diffDirectional(x1: float, x2: float) -> float:
    return (x2 - x1) / ((x1 + x2) / 2)

def differentSigns(x1: float, x2: float) -> bool:
    return (x1 < 0 and x2 > 0) or (x1 > 0 and x2 < 0)

def getTrend(values: List[float], maxLen: int, threshold: float) -> float:
    if len(values) < maxLen // 5:
        return 0

    result = diffDirectional(values[-maxLen // 5], values[-1])

    return 1 if result > threshold else -1 if result < -threshold else 0