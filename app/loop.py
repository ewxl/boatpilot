from time import time

class PILoop():
    def __init__(self,p,i,delta=None):
        self.p = p
        self.i = i
        self.isum = 0
        self.last = time()
        self.delta = delta if delta else lambda x,y: x-y
        self.target = 0

    def set(self,target):
        self.target = target

    def run(self,value):
        dtime = self.last-time()
        d = self.delta(value,self.target)
        self.isum += d*self.i*dtime
        return d*self.p+self.isum
