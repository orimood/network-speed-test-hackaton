
# Network Speed Test Application

![License](https://img.shields.io/badge/License-MIT-blue.svg)  
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)  
[![Repo Size](https://img.shields.io/github/repo-size/orimood/network-speed-test-hackaton)](https://github.com/orimood/network-speed-test-hackaton)

A Python-based client-server application for comparing TCP and UDP download speeds. Developed for the **Intro to Computer Networks 2024 Hackathon**, this project evaluates how network performance varies across different protocols, showcasing key networking concepts in a practical setup.

---

## 🌟 Features

- 📡 **Dynamic UDP Broadcasting**: Server continuously broadcasts availability to clients.  
- 🔄 **Simultaneous TCP & UDP Transfers**: Multiple concurrent connections for both protocols.  
- 📊 **Real-Time Performance Metrics**: Displays transfer speed, duration, and packet loss.  
- 💻 **Cross-Platform**: Runs seamlessly on macOS, Windows, and Linux.  
- 🧵 **Multithreaded Architecture**: Optimized for handling multiple connections without bottlenecks.  

---

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or newer  
- Git (for cloning the repository)  

### Installation

1. **Clone the repository**:  
    ```bash
    git clone https://github.com/orimood/network-speed-test-hackaton.git
    cd network-speed-test-hackaton
    ```

2. **Install dependencies**:  
    ```bash
    pip install -r requirements.txt
    ```

---

## ⚙️ Usage

### 1. Start the Server

The server broadcasts availability and handles download requests.  

```bash
python server.py
```

### 2. Run the Client

The client listens for server offers and initiates TCP/UDP downloads.  

```bash
python client.py
```

### 3. Input Configuration

During execution, the client will prompt for:  

- **File Size (bytes)**: Total data size to download.  
- **TCP Connections**: Number of simultaneous TCP downloads.  
- **UDP Connections**: Number of simultaneous UDP downloads.  

---

## 🔧 Configuration

Modify server parameters via environment variables or directly in `server.py`:  

| **Parameter**        | **Default** | **Description**                        |
|---------------------|-------------|----------------------------------------|
| `MAGIC_COOKIE`       | `0xabcddcba` | Authentication key for communication  |
| `UDP_PORT`           | `13117`     | Port for UDP broadcasting              |
| `TCP_PORT`           | `20000`     | Port for TCP connections               |
| `PAYLOAD_SIZE`       | `4096`      | Size of data packets (in bytes)        |
| `BROADCAST_INTERVAL` | `1.0` sec   | UDP broadcast interval (seconds)       |

---

## 📊 Sample Output

**Client Output:**  

```
📡 OS-assigned UDP port: 13117
🔎 Client started, listening for offers...
✅ Received offer from 192.168.1.5 on TCP port 20000
📂 Enter file size in bytes: 5000000
🔗 Enter number of TCP connections: 2
📡 Enter number of UDP connections: 2
📥 TCP transfer #1 finished, total time: 2.34 seconds, speed: 17.09 Mbps
📡 UDP transfer #1 finished, total time: 2.01 seconds, speed: 19.89 Mbps, success rate: 98.50%
🎉 All transfers complete, listening to offer requests...
```

**Server Output:**  

```
🎉 Server started at 192.168.1.5 on 2025-01-15 10:00:00
📡 UDP broadcast started at 2025-01-15 10:00:01
🦻 Listening on TCP port 20000
🦻 Listening on UDP port 13117
📊 Total TCP connections: 2
📊 Total data transferred: 10,000,000 bytes
❌ Server terminated.
```

---

## 📂 Project Structure

```
├── client.py             # Client-side logic
├── server.py             # Server-side logic
├── requirements.txt      # Python dependencies
├── README.md             # Project documentation
└── LICENSE               # MIT License
```



---

## 📜 License

This project is licensed under the MIT License.  
See the [LICENSE](LICENSE) file for more information.

---

## 📧 Contact

For any inquiries, please contact:
**Tomer Ovadya** – [E-Mail](mailto:ovadyat@post.bgu.ac.il)
**Ori Sinvani** – [E-Mail](mailto:orisin@post.bgu.ac.il)

