class Rotary():
    def __init__(self,callback):
        self.callback = callback
        self.value,self.min,self.max = 0,-1,1

    def btn_press(self,e):
        self.value,self.min,self.max = 0,-1,1
        self.callback(self.value,0)
        
    def edge(self,other):
        if self.value%2==other:
            self.value += 1
        else:
            self.value -= 1

        self.max = max(self.value,self.max)
        self.min = min(self.value,self.min)
        norm = (self.value-self.min)/(self.max-self.min)*2-1
        self.callback(self.value,norm)

