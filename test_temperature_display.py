import socket
import time
from SampleNetworkClient import SimpleNetworkClient

def test_temperature_display():
    # Test Case Description: Verify infant temperature line remains visible after unit switch
    print("Starting test_temperature_display")

    # Pre Condition: System running with unpatched code, ports active
    inf_port = 23456
    inc_port = 23457
    snc = SimpleNetworkClient(inf_port, inc_port)
    
    # Authenticate to get tokens
    inf_token = snc.authenticate(inf_port, b"!Q#E%T&U8i6y4r2w").decode("utf-8")
    inc_token = snc.authenticate(inc_port, b"!Q#E%T&U8i6y4r2w").decode("utf-8")
    assert inf_token, "Failed to authenticate infant thermometer"
    assert inc_token, "Failed to authenticate incubator thermometer"

    # Step 1: Get initial temperature in Celsius
    snc.setTemperatureC(inf_port, inf_token)
    time.sleep(1)  # Allow time for update
    initial_temp = snc.getTemperatureFromPort(inf_port, inf_token)
    assert initial_temp is not None, "Failed to retrieve initial temperature"

    # Step 2: Switch to Fahrenheit
    snc.setTemperatureF(inf_port, inf_token)
    time.sleep(1)
    f_temp = snc.getTemperatureFromPort(inf_port, inf_token)
    assert f_temp is not None, "Infant temperature disappeared after switching to Fahrenheit"
    # Verify conversion: Celsius to Fahrenheit (approx)
    expected_f = (initial_temp - 273) * 9 / 5 + 32
    assert abs(f_temp - expected_f) < 0.1, f"Expected {expected_f}, got {f_temp}"

    # Step 3: Switch back to Celsius
    snc.setTemperatureC(inf_port, inf_token)
    time.sleep(1)
    c_temp = snc.getTemperatureFromPort(inf_port, inf_token)
    assert c_temp is not None, "Infant temperature disappeared after switching back to Celsius"
    assert abs(c_temp - initial_temp) < 0.1, f"Expected {initial_temp}, got {c_temp}"

    # Post Condition: Infant temperature remains visible and correct
    print("Test passed: Infant temperature line remains visible and correct after unit switches")

    # Actual Result and Pass/Fail determined by assertions
    return True

if __name__ == "__main__":
    try:
        result = test_temperature_display()
        print("Pass/Fail: Pass" if result else "Pass/Fail: Fail")
    except Exception as e:
        print(f"Test failed: {e}")
        print("Pass/Fail: Fail")
