import gps
from time import time,sleep


g = gps.gps()
g.stream(gps.WATCH_ENABLE|gps.WATCH_PPS)

l = time()
st = 0
while True:

    while g.waiting():
        if st:
            print "waited",time()-st
            st = 0
        r = g.next()
        if r.get("class") != "TPV":
            continue

        t = time()
        d = t-l

        print t,d,r.get("class"),r.get("time","")
        l = t
        print r

    if not st:
        st = time()
    sleep(0.01)
