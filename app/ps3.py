from time import sleep
from approxeng.input.controllers import find_matching_controllers, ControllerRequirement
from approxeng.input.selectbinder import bind_controllers

import threading

class PS3:
    def __init__(self,callback):
        t = threading.Thread(None,self.loop,"ps3_loop",args=(callback,))
        t.start()

    def loop(self,callback):
        discovery = None
        # Look for an attached controller, requiring that it has 'lx' and 'ly' controls, looping until we find one.
        while discovery is None:
            try:
                discovery = find_matching_controllers(ControllerRequirement(require_snames=['lx', 'ly']))[0]
            except IOError:
                #print('No suitable controller found yet')
                sleep(2)

        # Bind the controller to the underlying event stream, returning a function used to tidy up
        unbind_function = bind_controllers(discovery, print_events=False)

        try:
            # Get a stream of values for the left stick x and y axes. If we were using robot code from gpio.zero we could
            # set the controller.stream[...] as a source, as sources are just iterators which produce sequences of values
            plx,ply,prx,pry = 0,0,0,0
            for lx, ly, rx, ry in discovery.controller.stream['lx', 'ly','rx', 'ry']:
                if plx != lx or ply != ly:
                    callback(dict(lx=lx,ly=ly))
                if prx != rx or pry != ry:
                    callback(dict(rx=rx,ry=ry))
                plx,ply,prx,pry = lx,ly,rx,ry
                sleep(0.05)
        except StopIteration:
            # Raised when the stream ends
            pass

        # Tidy up any resources (threads, file handles) used by the binder
        unbind_function()
