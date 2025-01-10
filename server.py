import socket
import threading
import struct
import time
import platform

# ANSI color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    BOLD = '\033[1m'
    ENDC = '\033[0m'

# Configuration
MAGIC_COOKIE = 0xabcddcba
OFFER_MSG_TYPE = 0x2
REQUEST_MSG_TYPE = 0x3
PAYLOAD_MSG_TYPE = 0x4
UDP_PORT = 13117
TCP_PORT = 20000
BUFFER_SIZE = 1024
BROADCAST_INTERVAL = 1  # seconds
PAYLOAD_SIZE = 1024  # Size of each UDP payload segment
TCP_BACKLOG = 5  # Maximum number of queued connections

# Global control for server threads
server_running = threading.Event()

# Statistics
total_tcp_connections = 0
total_data_transferred = 0  # in bytes


# Function Definitions
def create_udp_socket():
    """
    Create a UDP socket with cross-platform support.
    Uses SO_REUSEPORT on Linux/Unix and falls back to SO_REUSEADDR on Windows.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    if platform.system() != "Windows":
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            print(Colors.OKBLUE + "SO_REUSEPORT enabled for UDP socket." + Colors.ENDC)
        except AttributeError:
            print(Colors.WARNING + "SO_REUSEPORT not supported, falling back to SO_REUSEADDR." + Colors.ENDC)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    return sock


def udp_broadcast():
    """
    Periodically broadcasts a UDP offer message to announce the server.
    Logs "Broadcast sent" only once.
    """
    try:
        with create_udp_socket() as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            offer_msg = struct.pack('!IbHH', MAGIC_COOKIE, OFFER_MSG_TYPE, UDP_PORT, TCP_PORT)
            print(Colors.OKBLUE + "UDP broadcast started." + Colors.ENDC)

            broadcast_logged = False  # Track if the broadcast message has been logged

            while server_running.is_set():
                sock.sendto(offer_msg, ('<broadcast>', UDP_PORT))
                if not broadcast_logged:
                    print(Colors.OKGREEN + "Broadcast sent." + Colors.ENDC)
                    broadcast_logged = True  # Mark as logged to avoid repeated messages
                time.sleep(BROADCAST_INTERVAL)
    except Exception as e:
        print(Colors.FAIL + f"Error in UDP broadcast: {e}" + Colors.ENDC)



def handle_udp_connection():
    """
    Listens for incoming UDP requests and responds with data packets.
    Logs unexpected packets only once per IP address.
    """
    logged_ips = {}  # Dictionary to track IPs with unexpected packets

    try:
        with create_udp_socket() as udp_sock:
            udp_sock.bind(('', UDP_PORT))
            print(Colors.OKBLUE + f"Server started, listening on UDP port {UDP_PORT}" + Colors.ENDC)

            while server_running.is_set():
                udp_sock.settimeout(1)  # Avoid busy-waiting
                try:
                    data, addr = udp_sock.recvfrom(BUFFER_SIZE)
                    ip = addr[0]

                    # Check for packet length
                    if len(data) < 5:
                        if ip not in logged_ips:
                            logged_ips[ip] = True  # Mark IP as logged
                            print(Colors.WARNING + f"Invalid UDP packet from {ip}" + Colors.ENDC)
                        continue

                    # Unpack the request message
                    received_cookie, msg_type = struct.unpack('!Ib', data[:5])
                    if received_cookie != MAGIC_COOKIE or msg_type != REQUEST_MSG_TYPE:
                        if ip not in logged_ips:
                            logged_ips[ip] = True  # Mark IP as logged
                            print(Colors.FAIL + f"Invalid or unexpected packet from {ip}" + Colors.ENDC)
                        continue

                    # Valid request; remove IP from logged list
                    if ip in logged_ips:
                        del logged_ips[ip]

                    # Extract the file size from the request
                    file_size = struct.unpack('!Q', data[5:13])[0]
                    print(Colors.OKCYAN + f"UDP request from {addr}, file size: {file_size} bytes" + Colors.ENDC)

                    # Respond with payload packets
                    total_segments = (file_size + PAYLOAD_SIZE - 1) // PAYLOAD_SIZE
                    for segment in range(total_segments):
                        payload = struct.pack(
                            '!IbQQ',
                            MAGIC_COOKIE,
                            PAYLOAD_MSG_TYPE,
                            total_segments,
                            segment
                        ) + b'1' * (PAYLOAD_SIZE - 21)  # Fill remaining space with dummy data
                        udp_sock.sendto(payload, addr)
                        time.sleep(0.001)  # Simulate a slight delay for each packet
                except socket.timeout:
                    continue
    except Exception as e:
        print(Colors.FAIL + f"Error in UDP server: {e}" + Colors.ENDC)


def handle_tcp_connection(conn, addr):
    """
    Handles a single TCP connection. Receives the requested file size and sends the data.
    """
    global total_tcp_connections, total_data_transferred
    try:
        print(Colors.WARNING + f"New TCP connection from {addr}" + Colors.ENDC)
        file_size_data = conn.recv(BUFFER_SIZE)
        if not file_size_data:
            print(Colors.FAIL + f"Connection from {addr} closed unexpectedly." + Colors.ENDC)
            return

        try:
            file_size = int(file_size_data.decode().strip())
        except ValueError:
            print(Colors.FAIL + f"Invalid file size received from {addr}." + Colors.ENDC)
            return

        print(Colors.OKCYAN + f"File size requested by {addr}: {file_size} bytes" + Colors.ENDC)

        # Send the requested data
        data = b'1' * file_size
        conn.sendall(data)
        total_tcp_connections += 1
        total_data_transferred += file_size
        print(Colors.OKGREEN + f"Sent {file_size} bytes to {addr}." + Colors.ENDC)
    except Exception as e:
        print(Colors.FAIL + f"Error handling TCP connection from {addr}: {e}" + Colors.ENDC)
    finally:
        conn.close()


def tcp_server():
    """
    Listens for incoming TCP connections and handles them in separate threads.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
            server_sock.bind(('', TCP_PORT))
            server_sock.listen(TCP_BACKLOG)
            print(Colors.OKBLUE + f"Server started, listening on TCP port {TCP_PORT}" + Colors.ENDC)

            while server_running.is_set():
                server_sock.settimeout(1)
                try:
                    conn, addr = server_sock.accept()
                    threading.Thread(target=handle_tcp_connection, args=(conn, addr), daemon=True).start()
                except socket.timeout:
                    continue
    except Exception as e:
        print(Colors.FAIL + f"Error in TCP server: {e}" + Colors.ENDC)


def start_server():
    """
    Starts the server by initializing the UDP broadcaster, UDP server, and TCP server.
    """
    global total_tcp_connections, total_data_transferred
    try:
        server_running.set()
        print(Colors.HEADER + "Starting server..." + Colors.ENDC)

        # Start the UDP broadcaster
        threading.Thread(target=udp_broadcast, daemon=True, name="UDPBroadcaster").start()

        # Start the UDP server
        threading.Thread(target=handle_udp_connection, daemon=True, name="UDPServer").start()

        # Start the TCP server
        tcp_server()
    except KeyboardInterrupt:
        print(Colors.WARNING + "\nServer shutting down..." + Colors.ENDC)
        server_running.clear()
    except Exception as e:
        print(Colors.FAIL + f"Unexpected server error: {e}" + Colors.ENDC)
    finally:
        print(Colors.OKGREEN + "Server terminated." + Colors.ENDC)
        print(Colors.BOLD + Colors.OKCYAN + f"Total TCP connections handled: {total_tcp_connections}" + Colors.ENDC)
        print(Colors.BOLD + Colors.OKCYAN + f"Total data transferred: {total_data_transferred / (1024 * 1024):.2f} MB" + Colors.ENDC)


if __name__ == "__main__":
    start_server()
