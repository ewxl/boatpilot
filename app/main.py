import zmq
import json

from time import strptime,mktime,time
from functools import partial
from datetime import datetime
from os.path import isfile

from tornado.ioloop import IOLoop
from tornado import websocket,web,autoreload,gen

class WSHandler(websocket.WebSocketHandler):
    cl = []
    def open(self):
        #self.write_message(data)
        #self.write_message({'htrack':track})
        WSHandler.cl.append(self)

    def on_close(self):
        WSHandler.cl.remove(self)

    @staticmethod
    def write_all(msg):
        for c in WSHandler.cl:
            c.write_message(msg)

    def on_message(self,msg):
        msg = json.loads(msg)
        #WSHandler.write_all(data)
        App.socket.send_string("hello")

"<dictwrapper: {u'epx': 13.479, u'epy': 24.413, u'epv': 89.7, u'ept': 0.005, u'lon': 17.940367, u'eps': 16.61, u'epc': 61.02, u'lat': 59.521110374, u'track': 170.7872, u'mode': 3, u'time': u'2020-09-18T18:58:34.940Z', u'device': u'/dev/serial/by-id/usb-Prolific_Technology_Inc._USB-Serial_Controller-if00-port0', u'climb': -0.426, u'alt': 5.066, u'speed': 0.764, u'class': u'TPV'}>"

class App:
    def __init__(self,):
        self.g = None # gps context

        context = zmq.Context()
        App.socket = context.socket(zmq.PAIR)
        App.socket.connect("tcp://control:5556")
    
    @staticmethod
    def control_send(data):
        App.socket.send_string(data)

    async def control_com(socket):
        while True:
            try:
                message = App.socket.recv(flags=zmq.NOBLOCK)
                print ("Message received:", message)
            except zmq.Again as e:
                await gen.sleep(0.001)

def make_webserver():
    class MainHandler(web.RequestHandler):
        def get(self):
            self.render("static/index.htm")

    return web.Application([
                    (r"/", MainHandler),
                    (r"/static/(.*)", web.StaticFileHandler,{"path":"./static"}),
                    (r"/(favicon.*)", web.StaticFileHandler,{"path":"./static"}),
                    (r"/ws", WSHandler),
                    ],debug=True)

def main():
    wsapp = make_webserver()
    wsapp.listen(8000)

    app = App()
    
    IOLoop.current().spawn_callback(app.control_com)

    def graceful():
        for c in WSHandler.cl:
            c.close()
        print("Graceful reload.")

    autoreload.add_reload_hook(graceful)

    try:
        print("Ready.")
        IOLoop.current().start()
    finally:
        App.socket.close()
        for c in WSHandler.cl:
            c.close()
        print("Exit.")

if __name__ == "__main__":
    main()
