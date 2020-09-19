import tornado.ioloop
import tornado.websocket
import tornado.web
import gps
import json
from time import time
from datetime import datetime

from os.path import isfile

g = gps.gps(mode=gps.WATCH_ENABLE|gps.WATCH_PPS)
data = {'target_track':0,"moving":False,"Pk":0,"Ik":0,"out":0,"dsum":0}
logfile = None
track = []

if isfile("settings.json"):
    with open("settings.json","r") as r:
        data.update(json.loads(r.read()))

class WSHandler(tornado.websocket.WebSocketHandler):
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

        if "Pk" in data or "Ik" in data:
            with open("settings.json","w+") as w:
                w.write(json.dumps({"Pk":data.get("Pk"),"Ik":data.get("Ik")}))

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("static/index.htm")

def make_app():
    return tornado.web.Application([
                    (r"/", MainHandler),
                    (r"/static/(.*)", tornado.web.StaticFileHandler,{"path":"./static"}),
                    (r"/(favicon.ico)", tornado.web.StaticFileHandler,{"path":"./static"}),
                    (r"/ws", WSHandler),
                    ],debug=True)

"<dictwrapper: {u'epx': 13.479, u'epy': 24.413, u'epv': 89.7, u'ept': 0.005, u'lon': 17.940367, u'eps': 16.61, u'epc': 61.02, u'lat': 59.521110374, u'track': 170.7872, u'mode': 3, u'time': u'2020-09-18T18:58:34.940Z', u'device': u'/dev/serial/by-id/usb-Prolific_Technology_Inc._USB-Serial_Controller-if00-port0', u'climb': -0.426, u'alt': 5.066, u'speed': 0.764, u'class': u'TPV'}>"

def gps_handler():
    global logfile,track
    while g.waiting():
        r = g.next()
        if r.get("class") == "TPV":
            data.update(r)

            if not data.get("moving") and r.get("speed") > 1.5:
                data['moving'] = True
                
                logfile = open("track_{0}.log".format(datetime.utcnow().isoformat()),"w+")

            if data.get("moving") and r.get("speed") < 1:
                data['moving'] = False
                logfile.close()

            if data.get("moving"):
                logfile.write("{0},{lat},{lon},{track},{speed}\n".format(time(),**r))
                track.insert(0,(r.get("lat"),r.get("lon")))

                while len(track) > 300:
                    track.pop()
            
            for c in WSHandler.cl:
                c.write_message(data)

loop_int = 1000

def pi_loop():
    delta = (data.get("target_track",0)-data.get("track",0)+180)%360-180

    data["dsum"] += delta*data['Ik']*loop_int/1000
    data["out"] = delta*data.get("Pk")+data["dsum"]

    for c in WSHandler.cl:
        c.write_message({"out":data['out'],"dsum":data['dsum'],"delta":delta})

if __name__ == "__main__":
    app = make_app()
    app.listen(80)

    tornado.ioloop.PeriodicCallback(gps_handler,50).start()
    tornado.ioloop.PeriodicCallback(pi_loop,loop_int).start()
    tornado.ioloop.IOLoop.current().start()
