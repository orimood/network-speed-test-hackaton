import socket
import threading
import struct
import time
import platform
import os
import select  # For efficient socket polling

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
CONFIG = {
    "MAGIC_COOKIE": int(os.getenv("MAGIC_COOKIE", "0xabcddcba"), 16),
    "OFFER_MSG_TYPE": int(os.getenv("OFFER_MSG_TYPE", 2)),
    "REQUEST_MSG_TYPE": int(os.getenv("REQUEST_MSG_TYPE", 3)),
    "PAYLOAD_MSG_TYPE": int(os.getenv("PAYLOAD_MSG_TYPE", 4)),
    "UDP_PORT": int(os.getenv("UDP_PORT", 13117)),
    "TCP_PORT": int(os.getenv("TCP_PORT", 20000)),
    "BUFFER_SIZE": int(os.getenv("BUFFER_SIZE", 1024)),
    "BROADCAST_INTERVAL": float(os.getenv("BROADCAST_INTERVAL", 1.0)),
    "PAYLOAD_SIZE": int(os.getenv("PAYLOAD_SIZE", 4 * 1024)),
    "TCP_BACKLOG": int(os.getenv("TCP_BACKLOG", 5)),
}

# Global control for server threads
server_running = threading.Event()

# Statistics
total_tcp_connections = 0
total_data_transferred = 0  # in bytes

def get_server_ip():
    """Retrieve the server's local IP address."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]

def create_udp_socket():
    """Create a UDP socket with cross-platform support."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    if platform.system() != "Windows":
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        except AttributeError:
            pass
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    return sock

def udp_broadcast():
    """Periodically broadcasts a UDP offer message to announce the server."""
    try:
        with create_udp_socket() as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            offer_msg = struct.pack('!IbHH', CONFIG["MAGIC_COOKIE"], CONFIG["OFFER_MSG_TYPE"], CONFIG["UDP_PORT"], CONFIG["TCP_PORT"])
            print(Colors.OKBLUE + f"📡 UDP broadcast started at {time.strftime('%Y-%m-%d %H:%M:%S')}" + Colors.ENDC)

            while server_running.is_set():
                sock.sendto(offer_msg, ('<broadcast>', CONFIG["UDP_PORT"]))
                time.sleep(CONFIG["BROADCAST_INTERVAL"])
    except Exception as e:
        print(Colors.FAIL + f"❌ Error in UDP broadcast: {e}" + Colors.ENDC)

def handle_udp_connection():
    """Listens for incoming UDP requests and responds with data packets."""
    try:
        with create_udp_socket() as udp_sock:
            udp_sock.bind(('', CONFIG["UDP_PORT"]))
            print(Colors.OKGREEN + f"🦻 Listening on UDP port {CONFIG['UDP_PORT']}" + Colors.ENDC)

            while server_running.is_set():
                readable, _, _ = select.select([udp_sock], [], [], 1)
                for sock in readable:
                    data, addr = sock.recvfrom(CONFIG["BUFFER_SIZE"])
                    if len(data) < 5:
                        continue

                    cookie, msg_type = struct.unpack('!Ib', data[:5])
                    if cookie != CONFIG["MAGIC_COOKIE"] or msg_type != CONFIG["REQUEST_MSG_TYPE"]:
                        continue

                    file_size = struct.unpack('!Q', data[5:13])[0]
                    total_segments = (file_size + CONFIG["PAYLOAD_SIZE"] - 1) // CONFIG["PAYLOAD_SIZE"]

                    for segment in range(total_segments):
                        header = struct.pack('!IbQQ', CONFIG["MAGIC_COOKIE"], CONFIG["PAYLOAD_MSG_TYPE"], total_segments, segment)
                        payload_data = os.urandom(CONFIG["PAYLOAD_SIZE"] - len(header))
                        sock.sendto(header + payload_data, addr)
    except Exception as e:
        print(Colors.FAIL + f"❌ Error in UDP server: {e}" + Colors.ENDC)

def handle_tcp_connection(conn, addr):
    """Handles a single TCP connection, sending data in chunks."""
    global total_tcp_connections, total_data_transferred
    try:
        file_size_data = conn.recv(CONFIG["BUFFER_SIZE"])
        if not file_size_data:
            return

        file_size = int(file_size_data.decode().strip())
        chunk_size = 1024 * 1024  # 1 MB chunks

        for i in range(0, file_size, chunk_size):
            conn.sendall(b'1' * min(chunk_size, file_size - i))

        total_tcp_connections += 1
        total_data_transferred += file_size
    except Exception as e:
        print(Colors.FAIL + f"❌ Error handling TCP connection from {addr}: {e}" + Colors.ENDC)
    finally:
        conn.close()

def tcp_server():
    """Listens for incoming TCP connections and handles them with select()."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
            server_sock.bind(('', CONFIG["TCP_PORT"]))
            server_sock.listen(CONFIG["TCP_BACKLOG"])
            print(Colors.OKGREEN + f"🦻 Listening on TCP port {CONFIG['TCP_PORT']}" + Colors.ENDC)

            while server_running.is_set():
                readable, _, _ = select.select([server_sock], [], [], 1)
                for sock in readable:
                    conn, addr = sock.accept()
                    threading.Thread(target=handle_tcp_connection, args=(conn, addr), daemon=True).start()
    except Exception as e:
        print(Colors.FAIL + f"❌ Error in TCP server: {e}" + Colors.ENDC)

def start_server():
    """Starts the server with optimized socket handling."""
    global total_tcp_connections, total_data_transferred
    try:
        server_running.set()
        server_ip = get_server_ip()
        print(Colors.HEADER + f"🎉 Server started at {server_ip} on {time.strftime('%Y-%m-%d %H:%M:%S')}" + Colors.ENDC)

        threading.Thread(target=udp_broadcast, daemon=True).start()
        threading.Thread(target=handle_udp_connection, daemon=True).start()
        tcp_server()
    except KeyboardInterrupt:
        print(Colors.WARNING + "\n😔 Server shutting down..." + Colors.ENDC)
        server_running.clear()
    finally:
        print(Colors.OKGREEN + "❌ Server terminated." + Colors.ENDC)
        print(Colors.BOLD + Colors.OKCYAN + f"📊 Total TCP connections: {total_tcp_connections}" + Colors.ENDC)
        print(Colors.BOLD + Colors.OKCYAN + f"📊 Total data transferred: {total_data_transferred} bytes" + Colors.ENDC)

if __name__ == "__main__":
    start_server()
