import matplotlib.pyplot as plt
import matplotlib.animation as animation
import time
import math
import socket
import threading

class SimpleNetworkClient :
    def __init__(self, port1, port2) :
        now = time.time()
        self.lastTime = now
        self.times = [time.strftime("%H:%M:%S", time.localtime(now-i)) for i in range(30, 0, -1)]
        self.infTemps = [0]*30
        self.incTemps = [0]*30
        self.infPort = port1
        self.incPort = port2
        self.infToken = None
        self.incToken = None
        self.temp_lock = threading.Lock()  # Lock for thread-safe temperature access

    def updateTime(self) :
        now = time.time()
        if math.floor(now) > math.floor(self.lastTime) :
            t = time.strftime("%H:%M:%S", time.localtime(now))
            self.times.append(t)
            self.times = self.times[-30:]
            self.lastTime = now

    def convert_temperature(self, temp_k, unit):
        """Convert temperature from Kelvin to the specified unit."""
        if unit == "C":
            return temp_k - 273
        elif unit == "F":
            return (temp_k - 273) * 9 / 5 + 32
        return temp_k

    def getUnitFromPort(self, p, tok):
        """Retrieve the current unit setting from the thermometer."""
        payload = bytes((tok + ";GET_UNIT"), 'utf-8')
        s = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        try:
            s.sendto(payload, ("127.0.0.1", p))
            msg, addr = s.recvfrom(1024)
            unit = msg.decode("utf-8").strip()
            if unit in ["C", "F", "K"]:
                return unit
            return "K"  # Default to Kelvin if invalid
        except Exception as e:
            print(f"Error getting unit: {e}")
            return "K"  # Fallback to Kelvin on error

    def getTemperatureFromPort(self, p, tok) :
        """Retrieve temperature and convert to the current unit."""
        unit = self.getUnitFromPort(p, tok)
        payload = bytes((tok + ";GET_TEMP"), 'utf-8')
        s = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        try:
            s.sendto(payload, ("127.0.0.1", p))
            msg, addr = s.recvfrom(1024)
            temp_k = float(msg.decode("utf-8"))
            return self.convert_temperature(temp_k, unit), unit
        except Exception as e:
            print(f"Error getting temperature: {e}")
            return None, unit  # Return None for temperature on error

    def authenticate(self, p, pw) :
        s = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        try:
            s.sendto(b"AUTH %s;" % pw, ("127.0.0.1", p))
            msg, addr = s.recvfrom(1024)
            return msg.strip()
        except Exception as e:
            print(f"Authentication error: {e}")
            return None

    def setTemperatureC(self, p, tok):
        payload = bytes((tok + ";SET_DEGC"), 'utf-8')
        try:
            s = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
            s.sendto(payload, ("127.0.0.1", p))
            return True
        except Exception as ex:
            print(f"Error setting Celsius: {ex}")
            return False

    def setTemperatureF(self, p, tok):
        payload = bytes((tok + ";SET_DEGF"), 'utf-8')
        try:
            s = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
            s.sendto(payload, ("127.0.0.1", p))
            return True
        except Exception as ex:
            print(f"Error setting Fahrenheit: {ex}")
            return False

    def setTemperatureK(self, p, tok):
        payload = bytes((tok + ";SET_DEGK"), 'utf-8')
        try:
            s = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
            s.sendto(payload, ("127.0.0.1", p))
            return True
        except Exception as ex:
            print(f"Error setting Kelvin: {ex}")
            return False

    def updateInfTemp(self, p, tok) :
        self.updateTime()
        if self.infToken is None:  # Not yet authenticated
            self.infToken = self.authenticate(self.infPort, b"!Q#E%T&U8i6y4r2w")
        with self.temp_lock:
            temp, _ = self.getTemperatureFromPort(p, tok)
            if temp is not None:
                self.infTemps.append(temp)
                self.infTemps = self.infTemps[-30:]
        return self.infTemps

    def updateIncTemp(self, p, tok) :
        self.updateTime()
        if self.incToken is None:  # Not yet authenticated
            self.incToken = self.authenticate(self.incPort, b"!Q#E%T&U8i6y4r2w")
        with self.temp_lock:
            temp, _ = self.getTemperatureFromPort(p, tok)
            if temp is not None:
                self.incTemps.append(temp)
                self.incTemps = self.incTemps[-30:]
        return self.incTemps
