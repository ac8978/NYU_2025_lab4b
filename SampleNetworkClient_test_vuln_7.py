import matplotlib.pyplot as plt
import matplotlib.animation as animation
import time
import math
import socket

class SimpleNetworkClient:
    def __init__(self, port1, port2):
        now = time.time()
        self.lastTime = now
        self.times = [time.strftime("%H:%M:%S", time.localtime(now-i)) for i in range(30, 0, -1)]
        self.infTemps = [0]*30
        self.incTemps = [0]*30
        self.infPort = port1
        self.incPort = port2
        self.infToken = None
        self.incToken = None

    def updateTime(self):
        now = time.time()
        if math.floor(now) > math.floor(self.lastTime):
            t = time.strftime("%H:%M:%S", time.localtime(now))
            self.times.append(t)
            self.times = self.times[-30:]
            self.lastTime = now

    def getTemperatureFromPort(self, p, tok):
        payload = bytes((tok + ";GET_TEMP"), 'utf-8')
        s = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        s.sendto(payload, ("127.0.0.1", p))
        msg, addr = s.recvfrom(1024)
        m = msg.decode("utf-8")
        return float(m)

    def authenticate(self, p, pw):
        s = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        s.sendto(b"AUTH %s;" % pw, ("127.0.0.1", p))
        msg, addr = s.recvfrom(1024)
        return msg.strip()

    def setTemperatureC(self, p, tok):
        payload = bytes((tok + ";SET_DEGC"), 'utf-8')
        try:
            s = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
            s.sendto(payload, ("127.0.0.1", p))
        except Exception as ex:
            return False
        return True

    def setTemperatureF(self, p, tok):
        payload = bytes((tok + ";SET_DEGF"), 'utf-8')
        try:
            s = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
            s.sendto(payload, ("127.0.0.1", p))
        except Exception as ex:
            return False
        return True

    def setTemperatureK(self, p, tok):
        payload = bytes((tok + ";SET_DEGK"), 'utf-8')
        try:
            s = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
            s.sendto(payload, ("127.0.0.1", p))
        except Exception as ex:
            return False
        return True

    def updateInfTemp(self, p, tok):
        self.updateTime()
        if self.infToken is None:
            self.infToken = self.authenticate(self.infPort, b"!Q#E%T&U8i6y4r2w")
        self.infTemps.append(self.getTemperatureFromPort(p, tok)-273)
        self.infTemps = self.infTemps[-30:]
        self.infLn.set_data(range(30), self.infTemps)
        return self.infLn,

    def updateIncTemp(self, p, tok):
        self.updateTime()
        if self.incToken is None:
            self.incToken = self.authenticate(self.incPort, b"!Q#E%T&U8i6y4r2w")
        self.incTemps.append(self.getTemperatureFromPort(p, tok)-273)
        self.incTemps = self.incTemps[-30:]
        self.incLn.set_data(range(30), self.incTemps)
        return self.incLn,

    def test_input_validation(self, port, input_type="long_string"):
        """
        Sends malicious input to test server input validation.
        input_type: 'long_string' (50,000 bytes), 'many_semicolons' (5,000 semicolons), or 'invalid_utf8'
        """
        s = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        if input_type == "long_string":
            payload = bytes("A" * 50000, 'utf-8')  # 50,000 bytes, within UDP limit
            test_name = "Long String (50KB)"
        elif input_type == "many_semicolons":
            payload = bytes(";" * 5000, 'utf-8')  # 5,000 semicolons
            test_name = "Many Semicolons (5,000)"
        elif input_type == "invalid_utf8":
            payload = b'\xff\xfe' * 500  # Repeated invalid UTF-8 sequence
            test_name = "Invalid UTF-8 (1,000 bytes)"
        else:
            print(f"Invalid input_type: {input_type}")
            return

        print(f"\n=== Testing {test_name} on port {port} ===")
        try:
            print(f"Sending {test_name} payload (size: {len(payload)} bytes)...")
            s.sendto(payload, ("127.0.0.1", port))
            s.settimeout(5)
            msg, addr = s.recvfrom(1024)
            response = msg.decode("utf-8").strip()
            print(f"Server Response: {response}")
        except socket.timeout:
            response = "No response (possible server hang or crash)"
            print(response)
        except ConnectionRefusedError:
            response = "Server crashed or not running"
            print(response)
        except UnicodeDecodeError:
            response = "Server sent invalid UTF-8 response"
            print(response)
        except OSError as e:
            response = f"OS Error: {str(e)}"
            print(response)

        # Check if server is still responsive
        print(f"Checking server responsiveness...")
        try:
            s.sendto(b"AUTH !Q#E%T&U8i6y4r2w;", ("127.0.0.1", port))
            s.settimeout(5)
            msg, addr = s.recvfrom(1024)
            post_response = msg.decode("utf-8").strip()
            if len(post_response) == 16 and post_response.isalnum():
                print(f"Server is responsive (Received valid token: {post_response})")
            else:
                print(f"Server responded but with invalid token: {post_response}")
        except socket.timeout:
            print("Server is unresponsive after test")
        except ConnectionRefusedError:
            print("Server crashed after test")
        except UnicodeDecodeError:
            print("Server sent invalid UTF-8 response after test")
        except OSError as e:
            print(f"OS Error during responsiveness check: {str(e)}")
        finally:
            s.close()
        print(f"=== End of {test_name} Test ===\n")

if __name__ == "__main__":
    snc = SimpleNetworkClient(23456, 23457)
    # Run input validation tests
    snc.test_input_validation(23456, "long_string")
    snc.test_input_validation(23456, "many_semicolons")
    snc.test_input_validation(23456, "invalid_utf8")
