import zmq
import threading
import gps
import traceback
import json

from os.path import isfile
from time import sleep,time
from RPi import GPIO
#from influxdb import InfluxDBClient

from rotary import Rotary
from motor import Motor
from loop import PILoop

GPIO.setmode(GPIO.BCM)
btn,a,b = 14,18,23

GPIO.setup(btn,GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(a,GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(b,GPIO.IN, pull_up_down=GPIO.PUD_UP)

def gps_decode(r):
    if r.get("class") == "TPV":
        return dict(lon=r.get("lon"),lat=r.get("lat"),heading=r.get("track",0),speed=r.get("speed",0),)
    return {}

def is_moving(prev,speed):
    if not speed:
        return False

    if prev and speed < 1:
        return False

    if not prev and speed > 1.5:
        return True
    
    return prev

def main():
    data = {"heading":0,"speed":0,"Pt":0,"It":0,"Ps":0,"Is":0,"enable":0}

    if isfile("/etc/boatpilot/settings.json"):
        with open("/etc/boatpilot/settings.json","r") as r:
            data.update(json.loads(r.read()))

    context = zmq.Context()
    socket = context.socket(zmq.PAIR)
    socket.bind("tcp://*:5556")

    g = gps.gps(host="gpsd",mode=gps.WATCH_ENABLE|gps.WATCH_PPS)

    mtr = Motor(6,13,19,26)
    steering_wheel = Rotary(socket.send_string)

    GPIO.add_event_detect(btn,GPIO.RISING,callback=steering_wheel.btn_press)
    
    def _rotary_loop(call):
        while True:
            GPIO.wait_for_edge(a,GPIO.RISING if steering_wheel.value%2 else GPIO.FALLING)
            call(GPIO.input(b))

    t = threading.Thread(None,_rotary_loop,"rotary_loop",args=(steering_wheel.edge,))
    t.start()

    track_l = PILoop(data.get('Pt'),data.get('It'), delta = lambda x,y: (x-y+180)%360-180 )
    steer_l = PILoop(data.get('Ps'),data.get('Is'))

    try:
        print("Ready.")
        while True:
            sleep(0.005)
            while g.waiting():
                try:
                    data.update(**gps_decode(g.next()))
                except StopIteration:
                    print("Stop iteration in gpshandler")

            data['moving'] = is_moving(data.get("moving",0),data.get("speed",0))

            steer_l.set(track_l.run(data.get('heading')))
            m_out = steer_l.run(steering_wheel.value)

            #mtr.setspeed(m_out)

            if abs(m_out) < 1:
                mtr.stopMotor()
            else:
                mtr.startMotor()
                
            if m_out > mtr.speed:
                mtr.speed += 10
            elif m_out < mtr.speed:
                mtr.speed -= 10

            mtr.setDirection(m_out > 0)
            mtr.setSpeed(mtr.speed)

            # 4 times every second?
            #send(dict([(k,data.get(k)) for k in "steer rot dsum_steer dsum_track track".split()]))

            #save to influx every second?
            #"{lat},{lon},{track},{speed}".format(ts,**r))

            if False:
                save = "Pt,It,Ps,Is".split(",")
                if savefile:
                    with open("settings.json","w+") as w:
                        w.write(json.dumps(dict([(k,data.get(k,0)) for k in save])))
    
            try:
                r = socket.recv(flags=zmq.NOBLOCK)
                print(r)
                if r=="hello":
                    socket.send_string(json.dumps(data))
            except zmq.Again as e:
                pass


    except Exception as e:
        print("Exception: ",e)
        traceback.print_exc()
    GPIO.cleanup()
    
if __name__ == "__main__":
    main()
