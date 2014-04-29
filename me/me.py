import SocketServer
import time
import threading
import Queue

class Order:
    BUY  =  1
    SELL = -1

    def __init__(self, oid, qty, side, price):
        assert side in (Order.BUY, Order.SELL)
        self.oid    = oid
        self.qty    = qty
        self.side   = side
        self.price  = price

    def __str__(self):
        return str(self.qty)

class PriceLevel:
    def __init__(self, side, price):
        assert side in (Order.BUY, Order.SELL)
        self.side   = side
        self.price  = price
        self.orders = []

    def __str__(self):
        if self.side == Order.BUY:
            return " ".join(str(o) for o in reversed(self.orders))
        else:
            return " ".join(str(o) for o in          self.orders )

class Book:
    def __init__(self):
        self.prices = range(0,101)
        self.N      = len(self.prices)

        ## bids and asks, ordered lowest to highest price
        self.bids = [PriceLevel(Order.BUY,  p) for p in self.prices]
        self.asks = [PriceLevel(Order.SELL, p) for p in self.prices]

    def bidLevel(self, level=0):
        n = -1
        for i in reversed(xrange(self.N)):
            if len(self.bids[i].orders): n += 1
            if n == level:
                return self.bids[i]
        return None

    def askLevel(self, level=0):
        n = -1
        for i in xrange(self.N):
            if len(self.asks[i].orders): n += 1
            if n == level:
                return self.asks[i]
        return None

    def bid(self, level=0):
        b = self.bidLevel(level)
        if b is None: return None
        return b.price

    def ask(self, level=0):
        a = self.askLevel(level)
        if a is None: return None
        return a.price

    def addOrder(self, o):
        events = []

        ## (1) make all trades for resting orders that this new order crosses
        l = None
        while o.qty > 0:
            if l is None or len(l.orders) == 0:
                l = self.askLevel(0) if o.side == Order.BUY else self.bidLevel(0)
                ## if there are no remaining orders, there are definitely no more fills to do
                if l is None: break
            crossingPrice = (o.side == Order.BUY and l.price <= o.price) or (o.side == Order.SELL and l.price >= o.price)
            if crossingPrice:
                ro = l.orders[0]
                if ro.qty <= o.qty:
                    events.append(("eTradeOrder", ro.oid, ro.qty, ro.price))
                    o.qty  -= ro.qty
                    ro.qty  = 0
                    del l.orders[0]
                else:
                    events.append(("eTradeOrder", ro.oid,  o.qty, ro.price))
                    ro.qty -= o.qty
                    o.qty   = 0
            else:
                break ## prices don't cross

        ## (2) add this order to the book
        if o.qty > 0:
            (self.bids if o.side == Order.BUY else self.asks)[o.price].orders.append(o)
            events.append(("eAddOrder", o.oid, o.qty, o.side, o.price))

        return events

    def removeOrder(self, o):
        events = []
        restingOrders = (self.bids if o.side == Order.BUY else self.asks)[o.price].orders
        for ro in restingOrders:
            if ro.oid == o.oid:
                events.append(("eCancelOrder", ro.oid, ro.qty, ro.side, ro.price))
                restingOrders.remove(ro)
                break
        assert len(events) ## for now TODO: cancel rejects
        return events

    def __str__(self):
        bs = [str(l) for l in self.bids]
        ss = [str(l) for l in self.asks]
        W = 30
        fmt = "%%%ds %%03d %%-%ds" % (W, W)
        s = ""
        for i in reversed(xrange(self.N)):
            s += fmt % (bs[i][:W], self.prices[i], ss[i][:W]) + "\n"
        return s

if __name__ == "__main__":
    b = Book()

    print b.addOrder(Order(1, 10,Order.BUY ,67))
    print b.addOrder(Order(2,200,Order.SELL,68))
    print b.addOrder(Order(3, 11,Order.BUY ,67))
    print b.addOrder(Order(4,201,Order.SELL,68))
    print b.addOrder(Order(5, 15,Order.BUY ,67))
    print b.addOrder(Order(6, 15,Order.BUY ,68))
    print b.addOrder(Order(7,500,Order.BUY ,68))

    print b.removeOrder(Order(3, None,Order.BUY ,67))
    print b

    print b.bid(), "x",  b.ask()


##
##
##q = Queue.Queue()
##
##class GatewayTCPHandler(SocketServer.BaseRequestHandler):
##    """
##    The RequestHandler class for our server.
##
##    It is instantiated once per connection to the server, and must
##    override the handle() method to implement communication to the
##    client.
##    """
##
##    def handle(self):
##        ## self.request is the TCP socket connected to the client
##        self.data = self.request.recv(1024).strip()
##        print self.client_address, ": ", self.data
##        global q
##        q.put((self.client_address, self.data))
##
##class ThreadingTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer): pass
##
##if __name__ == "__main__":
##    HOST, PORT = "localhost", 9999
##
##    # Create the server, binding to localhost on port 9999
##    server = SocketServer.ThreadingTCPServer((HOST, PORT), GatewayTCPHandler)
##
##    t = threading.Thread(target=server.serve_forever)
##    t.daemon = True
##    t.start()
##
##    while True:
##        i = q.get()
##        print i, "START"
##        time.sleep(10)
##        print i, "DONE"
##