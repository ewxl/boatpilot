import zmq
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
from ps3 import PS3


def gps_decode(r):
    if r.get("class") == "TPV":
        return True,dict(lon=r.get("lon"),lat=r.get("lat"),heading=r.get("track",0),speed=r.get("speed",0),time=r.get("time"),)
    return False,{}

def is_moving(prev,speed):
    if not speed:
        return False

    if prev and speed < 1:
        return False

    if not prev and speed > 1.5:
        return True
    
    return prev

def main():
    data = {"heading":0,"speed":0,"Tp":0,"Ti":0,"Sp":0,"Si":0,"enable":0,'track_target':0}

    if isfile("/etc/boatpilot/settings.json"):
        with open("/etc/boatpilot/settings.json","r") as r:
            data.update(json.loads(r.read()))
        # TODO confirm they are floats in data, otherwise things go bad.

    context = zmq.Context()
    socket = context.socket(zmq.PAIR)
    socket.bind("ipc:///tmp/com")

    g = gps.gps(host="gpsd",mode=gps.WATCH_ENABLE|gps.WATCH_PPS)

    GPIO.setwarnings(False)

    GPIO.setmode(GPIO.BCM)
    mtr = Motor(6,13,19,26)

    steeringwheel = Rotary(14,18,23)

    def ps3_callback(value):
        socket.send_json(value)

    ps3 = PS3(ps3_callback)

    track_l = PILoop(data.get('Tp'),data.get('Ti'), delta = lambda x,y: (x-y+180)%360-180 )
    steer_l = PILoop(data.get('Sp'),data.get('Si'))
    rmin,rmax = -1,1
    
    looplast = 0
    try:
        print("Control ready.")
        while True:
            sleep(0.05)
            while g.waiting():
                try:
                    u,d = gps_decode(g.next())
                    if u:
                        data.update(**d)
                        socket.send_json(d)
                except StopIteration:
                    print("Stop iteration in gpshandler")

            value = None
            while not steeringwheel.q.empty():
                value = steeringwheel.q.get()
                if value is None:
                    rmin,rmax = -1,1

            if value is not None:
                rmax,rmin  = max(value,rmax), min(value,rmin)
                norm = (value-rmin)/(rmax-rmin)*2-1
                print("X"*value)
                socket.send_json({'steeringwheel':norm,'steeringwheel_abs':value})

            data['moving'] = is_moving(data.get("moving",0),data.get("speed",0))

            track_l_val = track_l.run(data.get('heading'))
            steer_l.set(track_l_val)
            m_out = steer_l.run(steeringwheel.value)

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

            if time() > looplast+1:
                socket.send_json(dict(track_l=track_l_val,m_out=m_out))
                looplast = time()

            # 4 times every second?
            #send(dict([(k,data.get(k)) for k in "steer rot dsum_steer dsum_track track".split()]))

            #save to influx every second?
            #"{lat},{lon},{track},{speed}".format(ts,**r))

            try:
                r = socket.recv_json(flags=zmq.NOBLOCK)
                if "ping" in r:
                    socket.send_json(data)
                    continue

                try:

                    if "set" in r:
                        updates = [k for k,v in r.get("set").items() if data[k]!=v]

                        for k,v in r.get("set",{}).items():
                            data[k] = v
                            if k=="Tp":
                                track_l.p = v

                            if k=="Ti":
                                track_l.i = v

                            if k=="Sp":
                                steer_l.p = v

                            if k=="Si":
                                steer_l.i = v
                        socket.send_json(dict([(k,data[k]) for k in updates]))

                        save = "Tp,Ti,Sp,Si".split(",")
                        with open("/etc/boatpilot/settings.json","w+") as w:
                            w.write(json.dumps(dict([(k,data.get(k,0)) for k in save]))+"\n")
                except Exception as ie:
                    print(ie)
                    traceback.print_exc()

            except zmq.Again as e:
                pass


    except Exception as e:
        print("Exception: ",e)
        traceback.print_exc()
    GPIO.cleanup()
    
if __name__ == "__main__":
    main()
