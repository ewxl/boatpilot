from RPi import GPIO
import zmq

GPIO.setmode(GPIO.BCM)

btn,a,b = 14,18,23
counter = 0
GPIO.setup(btn,GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(a,GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(b,GPIO.IN, pull_up_down=GPIO.PUD_UP)

ctx = zmq.Context()
skt = ctx.socket(zmq.PUB)
skt.bind("ipc:///tmp/rotary.enc")

def btn_press(e):
    global counter
    counter = 0
    skt.send("R"+str(counter))

GPIO.add_event_detect(btn,GPIO.RISING,callback=btn_press)

try:
    while True:
        GPIO.wait_for_edge(a, GPIO.FALLING if counter%2==0 else GPIO.RISING)
        dtState = GPIO.input(b)

        if counter%2==dtState:
            counter += 1
        else:
            counter -= 1
        skt.send("R"+str(counter))

except Exception, e:
    print("Exit",e)
