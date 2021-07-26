from RPi import GPIO

class Motor:
    def __init__(self,*args):
        for p in args:
            GPIO.setup(p,GPIO.OUT)
        self.apwm,self.a1,self.a2,self.stby = args
        self.pwm = GPIO.PWM(self.apwm,1000)
        self.speed = 0

    def startMotor(self):
        GPIO.output(self.stby,1)

    def setSpeed(self,speed):
        self.speed = speed
        self.pwm.start(min(100,abs(speed)))

    def setDirection(self,direction):
        GPIO.output(self.a1,not direction)
        GPIO.output(self.a2,direction)

    def stopMotor(self):
        GPIO.output(self.stby,0)


