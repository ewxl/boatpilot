from RPi import GPIO
import threading
import queue

class Rotary():
    def __init__(self,btn,a,b):
        self.btn,self.a,self.b = btn,a,b

        GPIO.setup(btn,GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(a,GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(b,GPIO.IN, pull_up_down=GPIO.PUD_UP)

        GPIO.add_event_detect(btn,GPIO.FALLING,callback=self.btn_press)
        self.q = queue.Queue()

        t = threading.Thread(None,self._rotary_loop,"rotary_loop")
        t.start()
    
    def _rotary_loop(self):
        self.value = 0
        while True:
            GPIO.wait_for_edge(self.a,GPIO.RISING)
            self.value += 1 if GPIO.input(self.b) else -1
            self.q.put(self.value)
            GPIO.wait_for_edge(self.a,GPIO.FALLING)
            self.value -= 1 if GPIO.input(self.b) else -1
            self.q.put(self.value)

    def btn_press(self,e):
        self.value = 0
        self.q.put( None )
        self.q.put( self.value )
