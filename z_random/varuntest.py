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
        

# The Python code below is the minimum code that is required in a submission file:
# 1. The "datamodel" imports at the top. Using the typing library is optional.
# 2. A class called "Trader", this class name should not be changed.
# 3. A run function that takes a tradingstate as input and outputs a "result" dict.

class Trader:

    pearlsBuyPos = 0
    pearlsSellPos = 0
    bananasPos = 0
    coconutsPos = 0
    pina_coladas = 0


    def run(self, state: TradingState) -> Dict[str, List[Order]]:
        
        #Holds all orders about to be executed
        result = {}

        #Holds all PEARL orders
        pearlOrders = []

        #Gets the current products
        products = state.order_depths.keys()

        

        #Prints out the current timestamp, buy orders, and sell orders for each product     
        for product in products:
            
            print("Current Timestamp: ", state.timestamp)
            print(product, " Buy Orders: ",state.order_depths[product].buy_orders)
            print(product, " Best Buy Order: ", self.bestBuyOrder(state,product))
            print(product, " Sell Orders: ",state.order_depths[product].sell_orders)
            print(product, " Best Sell Order: ", self.bestSellOrder(state,product))

        x = self.placeBuyOrder("PEARLS",5,self.bestBuyOrder(state,"PEARLS"))
        y = self.placeSellOrder("PEARLS",5,self.bestSellOrder(state,"PEARLS"))

        pearlOrders.append(x + 0.01)
        pearlOrders.append(y - 0.01)
        print("Current Position -- PEARL Buy Orders: ", self.pearlsBuyPos, " PEARL Sell Orders: ", self.pearlsSellPos)

        result["PEARLS"] = pearlOrders

        return result
        

    
    #Gets best Buy Order from the order book
    def bestBuyOrder(self, state: TradingState, product):
        buyOrders = state.order_depths[product].buy_orders
        Prices = list(buyOrders.keys())
        max = 0
        if len(Prices) != 0:
            for Price in Prices:
                if Price > max:
                    max = Price
        return(max)

    #Gets the best Sell Order from the order book
    def bestSellOrder(self, state: TradingState, product):
        sellOrders = state.order_depths[product].sell_orders
        Prices =  list(sellOrders.keys())
        if len(Prices) != 0:
            max = Prices[0]
            for Price in Prices:
                if Price < max:
                    max = Price
        return(max)
    
    def placeBuyOrder(self, product, quantity, price):
        currentOrder = Order(product, price, quantity)
        if(self.pearlBuyPos <= 15):
            self.pearlsBuyPos += quantity
        else:
            currentOrder = Order(product, price, 0)
            print("Cannot execute due to volume constraints")
            return currentOrder
        
        if(product == "PEARLS"):
            print("Pearl BUY Order Executed -- Price: ", price, " Quantity: ", quantity)
        
        return currentOrder
    
    def placeSellOrder(self, product, quantity, price):
        currentOrder = Order(product, price, -1 * quantity)
        if(self.pearlSellPos <= 15):
            self.pearlsSellPos += quantity
        else:
            currentOrder = Order(product, price, 0)
            print("Cannot execute due to volume constraints")
            return currentOrder
        if(product == "PEARLS"):
            print("Pearl SELL Order Executed -- Price: ", price, " Quantity: ", quantity)
        return currentOrder


        
      
                  


