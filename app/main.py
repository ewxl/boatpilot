import zmq
import gps
import json
from time import strptime,mktime
from datetime import datetime

from os.path import isfile
from RPi import GPIO
from tornado.ioloop import IOLoop,PeriodicCallback
from tornado import websocket,web,autoreload


data = {'target_track':0,"track":0,"moving":False,"Pkt":0,"Ikt":0,"Pks":0,"Iks":0,"dsum_track":0,"dsum_steer":0,"rot":0,"steer":0,"enable":0,'m_speed':0}
logfile = None
track = []

if isfile("settings.json"):
    with open("settings.json","r") as r:
        data.update(json.loads(r.read()))

GPIO.setmode(GPIO.BCM)

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

mtr = Motor(6,13,19,26)

class WSHandler(websocket.WebSocketHandler):
    cl = []
    def open(self):
        global track
        self.write_message(data)

        self.write_message({'htrack':track})
        WSHandler.cl.append(self)

    def on_close(self):
        WSHandler.cl.remove(self)

    def on_message(self,msg):
        msg = json.loads(msg)
        if "add" in msg:
            data['target_track'] += msg.get("add",0)
            data['target_track'] %= 360
            self.write_message({"target_track":data.get("target_track")})
            return

        data.update(msg)

        for c in WSHandler.cl:
            c.write_message(data)

        savefile = False
        save = "Pkt,Ikt,Pks,Iks".split(",")

        for key,val in msg.items():
            if key=="m_speed":
                mtr.setSpeed(abs(val))
                mtr.setDirection(val > 0)
                if abs(val) > 1:
                    mtr.startMotor()
                else:
                    mtr.stopMotor()

            if key=="enable":
                if val:
                    data['target_track'] = data['track']
                else:
                    mtr.stopMotor()
                    
            if key in save:
                savefile = True

        if savefile:
            with open("settings.json","w+") as w:
                w.write(json.dumps(dict([(k,data.get(k,0)) for k in save])))

class MainHandler(web.RequestHandler):
    def get(self):
        self.render("static/index.htm")

def make_app():
    return web.Application([
                    (r"/", MainHandler),
                    (r"/static/(.*)", web.StaticFileHandler,{"path":"./static"}),
                    (r"/(favicon.ico)", web.StaticFileHandler,{"path":"./static"}),
                    (r"/ws", WSHandler),
                    ],debug=True)

"<dictwrapper: {u'epx': 13.479, u'epy': 24.413, u'epv': 89.7, u'ept': 0.005, u'lon': 17.940367, u'eps': 16.61, u'epc': 61.02, u'lat': 59.521110374, u'track': 170.7872, u'mode': 3, u'time': u'2020-09-18T18:58:34.940Z', u'device': u'/dev/serial/by-id/usb-Prolific_Technology_Inc._USB-Serial_Controller-if00-port0', u'climb': -0.426, u'alt': 5.066, u'speed': 0.764, u'class': u'TPV'}>"
g = None

def gps_handler():
    global logfile,track,g
    if g is None:
        g = gps.gps(host="gpsd",mode=gps.WATCH_ENABLE|gps.WATCH_PPS)
    while g.waiting():
        try:
            r = g.next()
        except StopIteration:
            g = None
            break
        if r.get("class") == "TPV":
            data.update(r)

            ts = mktime(strptime(r.get('time')[:-5],"%Y-%m-%dT%H:%M:%S"))
            dt = datetime.fromtimestamp(ts)

            if not data.get("moving") and r.get("speed") > 1.5:
                data['moving'] = True
                logfile = open("track_{0}.log".format(dt.isoformat()),"w+")

            if data.get("moving") and r.get("speed") < 1:
                data['moving'] = False
                logfile.close()

            if data.get("moving"):
                logfile.write("{0},{lat},{lon},{track},{speed}\n".format(ts,**r))
                track.insert(0,(r.get("lat"),r.get("lon")))

                while len(track) > 300:
                    track.pop()
            
            for c in WSHandler.cl:
                c.write_message(dict(r))
                c.write_message({'moving':data['moving']})

PI_INT_TRACK = 1000
PI_INT_STEER = 200

def pi_track_loop():
    if not data.get("enable"):
        return
    delta = (data.get("target_track",0)-data.get("track",0)+180)%360-180
    data["dsum_track"] += delta*data['Ikt']*PI_INT_TRACK/1000
    data["steer"] = delta*data.get("Pkt")+data["dsum_track"]

    for c in WSHandler.cl:
        c.write_message(
                dict([(k,data.get(k)) for k in "steer rot dsum_steer dsum_track track".split()])
                )

def pi_steer_loop():
    if not data.get("enable"):
        return
    delta = data.get("steer",0)-data.get("rot",0)
    data["dsum_steer"] += delta*data['Iks']*PI_INT_STEER/1000

    out = delta*data.get("Pks")+data["dsum_steer"]

    if abs(out) < 1:
        mtr.stopMotor()
    else:
        mtr.startMotor()
        
    if out > mtr.speed:
        mtr.speed += 10
    elif out < mtr.speed:
        mtr.speed -= 10

    mtr.setDirection(out > 0)
    mtr.setSpeed(mtr.speed)

ctx = zmq.Context()
skt = ctx.socket(zmq.SUB)

skt.connect("ipc:///tmp/rotary.enc")
skt.setsockopt(zmq.SUBSCRIBE,b"R")

def z_recv():
    try:
        while True:
            d = skt.recv(flags=zmq.NOBLOCK)
            data['rot'] = -int(d[1:])
            for c in WSHandler.cl:
                c.write_message({"rot":data['rot']})

    except zmq.Again:
        pass

if __name__ == "__main__":

    app = make_app()
    app.listen(80)

    PeriodicCallback(gps_handler,50).start()
    PeriodicCallback(z_recv,50).start()
    PeriodicCallback(pi_track_loop,PI_INT_TRACK).start()
    PeriodicCallback(pi_steer_loop,PI_INT_STEER).start()

    def graceful():
        GPIO.cleanup()

    autoreload.add_reload_hook(graceful)

    try:
        print("Running...")
        IOLoop.current().start()
    finally:
        GPIO.cleanup()
