import socket
import threading
import struct
import time

# Configuration
MAGIC_COOKIE = 0xabcddcba
OFFER_MSG_TYPE = 0x2
UDP_PORT = 13117
TCP_PORT = 20000
BUFFER_SIZE = 1024
BROADCAST_INTERVAL = 1  # seconds
TCP_BACKLOG = 5  # Max queued connections

def udp_broadcast():
    """
    Periodically broadcasts a UDP offer message to announce the server.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            offer_msg = struct.pack('!IbHH', MAGIC_COOKIE, OFFER_MSG_TYPE, UDP_PORT, TCP_PORT)
            print("UDP broadcast started.")
            while True:
                sock.sendto(offer_msg, ('<broadcast>', UDP_PORT))
                print("Broadcast sent.")
                time.sleep(BROADCAST_INTERVAL)
    except Exception as e:
        print(f"Error in UDP broadcast: {e}")

def handle_tcp_connection(conn, addr):
    """
    Handles a single TCP connection. Receives the requested file size and sends the data.
    """
    try:
        print(f"New connection from {addr}")
        # Receive file size
        file_size_data = conn.recv(BUFFER_SIZE)
        if not file_size_data:
            print(f"Connection from {addr} closed unexpectedly.")
            return

        file_size = int(file_size_data.decode().strip())
        print(f"File size requested by {addr}: {file_size} bytes")

        # Send the requested data
        data = b'1' * file_size
        conn.sendall(data)
        print(f"Sent {file_size} bytes to {addr}.")
    except Exception as e:
        print(f"Error handling TCP connection from {addr}: {e}")
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
            print(f"Server started, listening on TCP port {TCP_PORT}")
            while True:
                conn, addr = server_sock.accept()
                threading.Thread(target=handle_tcp_connection, args=(conn, addr), daemon=True, name=f"TCPHandler-{addr}").start()
    except Exception as e:
        print(f"Error in TCP server: {e}")

def start_server():
    """
    Starts the server by initializing the UDP broadcaster and TCP server.
    """
    try:
        print("Starting server...")
        threading.Thread(target=udp_broadcast, daemon=True, name="UDPBroadcaster").start()
        tcp_server()
    except KeyboardInterrupt:
        print("Server shutting down...")
    except Exception as e:
        print(f"Unexpected server error: {e}")

if __name__ == "__main__":
    start_server()
