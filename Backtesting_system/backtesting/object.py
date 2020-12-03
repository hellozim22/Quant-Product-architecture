from dataclasses import dataclass

@dataclass
class TradeData():
    """
    Trade data contains information of a fill of an order. One order
    can have several trade fills.
    """

    symbol: str
    direction: str
    offset: str
    price: float = 0
    volume: float = 0
    time: str = ""

    def __init__(self,symbol,direction,offset,price,volume,time):
        """"""
        self.symbol = symbol
        self.direction = direction
        self.offset = offset
        self.price = price
        self.volume = volume
        self.time = time

