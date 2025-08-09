import threading
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import infinc
import time
import math
import socket
import fcntl
import os
import errno
import random
import string


class SmartNetworkThermometer (threading.Thread) :
    open_cmds = ["AUTH", "LOGOUT"]
    prot_cmds = ["SET_DEGF", "SET_DEGC", "SET_DEGK", "GET_TEMP", "UPDATE_TEMP", "GET_UNIT"]

    def __init__ (self, source, updatePeriod, port) :
        threading.Thread.__init__(self, daemon = True) 
        self.source = source
        self.updatePeriod = updatePeriod
        self.curTemperature = 0
        self.updateTemperature()
        self.tokens = []
        self.deg = "K"  # Default unit is Kelvin
        self.unit_lock = threading.Lock()  # Lock for thread-safe unit changes

        self.serverSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self.serverSocket.bind(("127.0.0.1", port))
        fcntl.fcntl(self.serverSocket, fcntl.F_SETFL, os.O_NONBLOCK)

    def setSource(self, source) :
        self.source = source

    def setUpdatePeriod(self, updatePeriod) :
        self.updatePeriod = updatePeriod 

    def setDegreeUnit(self, s) :
        with self.unit_lock:
            self.deg = s
            if self.deg not in ["F", "K", "C"] :
                self.deg = "K"

    def getDegreeUnit(self):
        with self.unit_lock:
            return self.deg

    def updateTemperature(self) :
        self.curTemperature = self.source.getTemperature()

    def getTemperature(self) :
        # Always return temperature in Kelvin; let client handle conversions
        return self.curTemperature

    def processCommands(self, msg, addr) :
        cmds = msg.split(';')
        for c in cmds :
            cs = c.split(' ')
            if len(cs) == 2 : #should be either AUTH or LOGOUT
                if cs[0] == "AUTH":
                    if cs[1] == "!Q#E%T&U8i6y4r2w" :
                        self.tokens.append(''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(16)))
                        self.serverSocket.sendto(self.tokens[-1].encode("utf-8"), addr)
                    else:
                        self.serverSocket.sendto("Incorrect password".encode("utf-8"), addr)
                elif cs[0] == "LOGOUT":
                    if cs[1] in self.tokens :
                        self.tokens.remove(cs[1])
                else : #unknown command
                    self.serverSocket.sendto(b"Invalid Command\n", addr)
            elif c == "SET_DEGF" :
                self.setDegreeUnit("F")
            elif c == "SET_DEGC" :
                self.setDegreeUnit("C")
            elif c == "SET_DEGK" :
                self.setDegreeUnit("K")
            elif c == "GET_TEMP" :
                self.serverSocket.sendto(b"%f\n" % self.getTemperature(), addr)
            elif c == "UPDATE_TEMP" :
                self.updateTemperature()
            elif c == "GET_UNIT" :
                self.serverSocket.sendto(self.getDegreeUnit().encode("utf-8"), addr)
            elif c :
                self.serverSocket.sendto(b"Invalid Command\n", addr)

    def run(self) : #the running function
        while True : 
            try :
                msg, addr = self.serverSocket.recvfrom(1024)
                msg = msg.decode("utf-8").strip()
                cmds = msg.split(' ')
                if len(cmds) == 1 : # protected commands case
                    semi = msg.find(';')
                    if semi != -1 : #if we found the semicolon
                        if msg[:semi] in self.tokens : #if its a valid token
                            self.processCommands(msg[semi+1:], addr)
                        else :
                            self.serverSocket.sendto(b"Bad Token\n", addr)
                    else :
                        self.serverSocket.sendto(b"Bad Command\n", addr)
                elif len(cmds) == 2 :
                    if cmds[0] in self.open_cmds : #if its AUTH or LOGOUT
                        self.processCommands(msg, addr) 
                    else :
                        self.serverSocket.sendto(b"Authenticate First\n", addr)
                else :
                    # otherwise bad command
                    self.serverSocket.sendto(b"Bad Command\n", addr)
    
            except IOError as e :
                if e.errno == errno.EWOULDBLOCK :
                    pass
                else :
                    pass
                msg = ""

            self.updateTemperature()
            time.sleep(self.updatePeriod)


class SimpleClient :
    def __init__(self, therm1, therm2) :
        self.fig, self.ax = plt.subplots()
        now = time.time()
        self.lastTime = now
        self.times = [time.strftime("%H:%M:%S", time.localtime(now-i)) for i in range(30, 0, -1)]
        self.infTemps = [0]*30
        self.incTemps = [0]*30
        self.infLn, = plt.plot(range(30), self.infTemps, label="Infant Temperature")
        self.incLn, = plt.plot(range(30), self.incTemps, label="Incubator Temperature")
        plt.xticks(range(30), self.times, rotation=45)
        plt.ylim((20, 50))
        plt.ylabel("Temperature (°C)")
        plt.legend(handles=[self.infLn, self.incLn])
        self.infTherm = therm1
        self.incTherm = therm2
        self.temp_lock = threading.Lock()  # Lock for thread-safe temperature access

        self.ani = animation.FuncAnimation(self.fig, self.updateInfTemp, interval=500)
        self.ani2 = animation.FuncAnimation(self.fig, self.updateIncTemp, interval=500)

    def convert_to_celsius(self, temp_k):
        """Convert temperature from Kelvin to Celsius."""
        return temp_k - 273

    def updateTime(self) :
        now = time.time()
        if math.floor(now) > math.floor(self.lastTime) :
            t = time.strftime("%H:%M:%S", time.localtime(now))
            self.times.append(t)
            self.times = self.times[-30:]
            self.lastTime = now
            plt.xticks(range(30), self.times, rotation=45)
            plt.title(time.strftime("%A, %Y-%m-%d", time.localtime(now)))

    def updateInfTemp(self, frame) :
        self.updateTime()
        with self.temp_lock:
            temp_k = self.infTherm.getTemperature()
            self.infTemps.append(self.convert_to_celsius(temp_k))
            self.infTemps = self.infTemps[-30:]
            self.infLn.set_data(range(30), self.infTemps)
        return self.infLn,

    def updateIncTemp(self, frame) :
        self.updateTime()
        with self.temp_lock:
            temp_k = self.incTherm.getTemperature()
            self.incTemps.append(self.convert_to_celsius(temp_k))
            self.incTemps = self.incTemps[-30:]
            self.incLn.set_data(range(30), self.incTemps)
        return self.incLn,

UPDATE_PERIOD = .05 #in seconds
SIMULATION_STEP = .1 #in seconds

bob = infinc.Human(mass = 8, length = 1.68, temperature = 36 + 273)
bobThermo = SmartNetworkThermometer(bob, UPDATE_PERIOD, 23456)
bobThermo.start()

inc = infinc.Incubator(width = 1, depth=1, height = 1, temperature = 37 + 273, roomTemperature = 20 + 273)
incThermo = SmartNetworkThermometer(inc, UPDATE_PERIOD, 23457)
incThermo.start()

incHeater = infinc.SmartHeater(powerOutput = 1500, setTemperature = 45 + 273, thermometer = incThermo, updatePeriod = UPDATE_PERIOD)
inc.setHeater(incHeater)
incHeater.start()

sim = infinc.Simulator(infant = bob, incubator = inc, roomTemp = 20 + 273, timeStep = SIMULATION_STEP, sleepTime = SIMULATION_STEP / 10)
sim.start()

sc = SimpleClient(bobThermo, incThermo)

plt.grid()
plt.show()
