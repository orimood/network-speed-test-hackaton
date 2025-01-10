import socket
import threading
import struct
import time

# ANSI color codes for terminal output
# ANSI color codes for terminal output
class Colors:
    # Text Colors
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    LIGHTGREY = '\033[37m'
    DARKGREY = '\033[90m'
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[97m'

    # Background Colors
    BG_BLACK = '\033[40m'
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    BG_MAGENTA = '\033[45m'
    BG_CYAN = '\033[46m'
    BG_WHITE = '\033[107m'

    # Text Formatting
    BOLD = '\033[1m'
    DIM = '\033[2m'
    ITALIC = '\033[3m'
    UNDERLINE = '\033[4m'
    BLINK = '\033[5m'
    REVERSE = '\033[7m'
    HIDDEN = '\033[8m'
    STRIKETHROUGH = '\033[9m'

    # Reset
    ENDC = '\033[0m'

# Configuration
MAGIC_COOKIE = 0xabcddcba
OFFER_MSG_TYPE = 0x2
UDP_PORT = 13117
TCP_PORT = 20000
BUFFER_SIZE = 1024
BROADCAST_INTERVAL = 1  # seconds
TCP_BACKLOG = 5  # Max queued connections

# Event to control server running
server_running = threading.Event()
broadcast_logged = threading.Event()  # Control printing of "Broadcast sent"

# Statistics
total_tcp_connections = 0
total_data_transferred = 0  # in bytes

def udp_broadcast():
    """
    Periodically broadcasts a UDP offer message to announce the server.
    Logs "Broadcast sent" only once, while continuously broadcasting.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            offer_msg = struct.pack('!IbHH', MAGIC_COOKIE, OFFER_MSG_TYPE, UDP_PORT, TCP_PORT)
            print(Colors.OKBLUE + "UDP broadcast started." + Colors.ENDC)
            while server_running.is_set():
                sock.sendto(offer_msg, ('<broadcast>', UDP_PORT))
                if not broadcast_logged.is_set():
                    print(Colors.OKGREEN + "Broadcast sent." + Colors.ENDC)
                    broadcast_logged.set()
                time.sleep(BROADCAST_INTERVAL)
    except Exception as e:
        print(Colors.FAIL + f"Error in UDP broadcast: {e}" + Colors.ENDC)

def handle_tcp_connection(conn, addr):
    """
    Handles a single TCP connection. Receives the requested file size and sends the data.
    """
    global total_tcp_connections, total_data_transferred
    try:
        print(Colors.WARNING + f"New connection from {addr}" + Colors.ENDC)
        # Receive file size
        file_size_data = conn.recv(BUFFER_SIZE)
        if not file_size_data:
            print(Colors.FAIL + f"Connection from {addr} closed unexpectedly." + Colors.ENDC)
            return

        # Validate file size input
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
                server_sock.settimeout(1)  # Allow periodic checks for the server_running event
                try:
                    conn, addr = server_sock.accept()
                    threading.Thread(target=handle_tcp_connection, args=(conn, addr), daemon=True).start()
                except socket.timeout:
                    continue
    except Exception as e:
        print(Colors.FAIL + f"Error in TCP server: {e}" + Colors.ENDC)

def start_server():
    """
    Starts the server by initializing the UDP broadcaster and TCP server.
    Collects and displays statistics upon shutdown.
    """
    global total_tcp_connections, total_data_transferred
    try:
        server_running.set()  # Signal threads to run
        print(Colors.HEADER + "Starting server..." + Colors.ENDC)
        threading.Thread(target=udp_broadcast, daemon=True, name="UDPBroadcaster").start()
        tcp_server()
    except KeyboardInterrupt:
        print(Colors.WARNING + "\nServer shutting down..." + Colors.ENDC)
        server_running.clear()  # Signal threads to stop
    except Exception as e:
        print(Colors.FAIL + f"Unexpected server error: {e}" + Colors.ENDC)
    finally:
        print(Colors.OKGREEN + "Server terminated." + Colors.ENDC)
        print(Colors.BOLD + Colors.OKCYAN + f"Total TCP connections handled: {total_tcp_connections}" + Colors.ENDC)
        print(Colors.BOLD + Colors.OKCYAN + f"Total data transferred: {total_data_transferred / (1024 * 1024):.2f} MB" + Colors.ENDC)

if __name__ == "__main__":
    start_server()
