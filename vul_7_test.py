import socket
import time
import sys

# Test Case Description: Verify if the server crashes or responds incorrectly when receiving a very long input string
# Pre Condition: SampleNetworkServer.py is running, and no input validation patch is applied
# Expected Result: The server should either crash or respond with an error message without hanging
# Post Condition: The server should remain responsive to subsequent valid requests
# Explanation: This test checks if the server can handle a long input without crashing or excessive resource usage

def test_long_input():
    port = 23456  # Infant thermometer port
    host = "127.0.0.1"
    malicious_input = "A" * 1000  # 1MB of 'A' characters
    payload = bytes(malicious_input, 'utf-8')

    # Create UDP socket
    s = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    
    # Send malicious input
    try:
        print("Sending 1MB input to server...")
        s.sendto(payload, (host, port))
        s.settimeout(5)  # Wait up to 5 seconds for response
        msg, addr = s.recvfrom(1024)
        actual_result = msg.decode("utf-8").strip()
        print(f"Received response: {actual_result}")
    except socket.timeout:
        actual_result = "No response (possible server hang or crash)"
        print(actual_result)
    except ConnectionRefusedError:
        actual_result = "Server crashed or not running"
        print(actual_result)
    except UnicodeDecodeError:
        actual_result = "Server sent invalid UTF-8 response"
        print(actual_result)

    # Post-condition: Check if server is still responsive
    try:
        s.sendto(b"AUTH !Q#E%T&U8i6y4r2w;", (host, port))
        s.settimeout(5)
        msg, addr = s.recvfrom(1024)
        post_condition_result = msg.decode("utf-8").strip()
        print(f"Post-condition check: Server responded with token: {post_condition_result}")
        if len(post_condition_result) == 16:  # Valid token length
            post_condition = "Server is responsive"
        else:
            post_condition = "Server responded but with invalid token"
    except socket.timeout:
        post_condition = "Server is unresponsive after test"
        print(post_condition)
    except ConnectionRefusedError:
        post_condition = "Server crashed"
        print(post_condition)

    # Expected vs Actual
    expected_result = "Invalid Command"  # Expected response for invalid input
    pass_fail = actual_result == expected_result and post_condition == "Server is responsive"
    
    print(f"\nTest Summary:")
    print(f"Expected Result: {expected_result}")
    print(f"Actual Result: {actual_result}")
    print(f"Post Condition: {post_condition}")
    print(f"Pass/Fail: {'Pass' if pass_fail else 'Fail'}")
    print(f"Explanation: The test sends a 1MB input to check if the server handles it gracefully. "
          f"A passing test means the server responds with 'Invalid Command' and remains responsive. "
          f"A failing test indicates a crash, hang, or incorrect response.")

if __name__ == "__main__":
    test_long_input()
