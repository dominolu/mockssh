import socket
import datetime
from datetime import datetime
import os
import subprocess
import json
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import threading
import fcntl
import time
from loguru import logger

# 配置logger
logger.add("mockssh.log", rotation="500 MB", level="INFO")

# 基础配置
CONFIG_FILE = "config.json"
BANNED_IPS_FILE = "banned_ips.txt"

banned_ips=set()

def load_banned_ips():
    """从文件加载已封禁的IP列表"""
    try:
        config = load_config()
        banned_ips_file = config["files"]["banned_ips"]
        if os.path.exists(banned_ips_file):
            with open(banned_ips_file, 'r') as f:
                return set(line.strip() for line in f if line.strip())
        return set()
    except Exception as e:
        logger.error(f"Error loading banned IPs: {e}")
        return set()

def save_banned_ips(new_ips):
    """保存封禁的IP到文件"""
    global banned_ips
    try:
        config = load_config()
        banned_ips_file = config["files"]["banned_ips"]
        with open(banned_ips_file, 'a') as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            try:
                for ip in new_ips:
                    f.write(f"{ip}\n")
                    banned_ips.add(ip)
                f.flush()
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        return True
    except Exception as e:
        logger.error(f"Error saving banned IPs: {e}")
        return False

def init_firebase():
    """初始化 Firebase 连接"""
    try:
        cfg=load_config()
        FIREBASE_CRED_FILE = cfg["files"]["firebase_credentials"]
        URL=cfg["firebase_url"]
        cred = credentials.Certificate(FIREBASE_CRED_FILE)
        firebase_admin.initialize_app(cred, {
            'databaseURL': URL
        })
        logger.info("Firebase initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Firebase: {e}")
        raise

def load_config():
    """加载本地配置"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {
        "network": {
            "host": "0.0.0.0",
            "port": 22
        },
        "files": {
            "firebase_credentials": "firebase-credentials.json",
            "banned_ips": "banned_ips.txt"
        },
        "firebase_url": "Your Firebase Realtime Database URL",
        "last_sync_id": 0
    }

def save_config(config):
    """保存配置到本地"""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f)

def get_banned_ips():
    """获取当前 fail2ban 已封禁的 IP"""
    try:
        result = subprocess.run(["fail2ban-client", "status", "sshd"], 
                              capture_output=True, 
                              text=True,
                              check=True)
        # 解析输出获取已封禁 IP
        banned = []
        for line in result.stdout.split('\n'):
            if "Banned IP list:" in line:
                banned = line.split(':')[1].strip().split()
        return set(banned)
    except Exception as e:
        logger.error(f"Error getting banned IPs: {e}")
        return set()

def sync_ips(newip):
    """同步新的 IP 并更新 fail2ban"""
    global banned_ips
    try:
        config = load_config()
        last_id = config.get("last_sync_id", 0)
        
        # 获取 Firebase 中的新记录
        ref = db.reference('banned_ips')
        new_records = ref.order_by_child('id').start_at(last_id + 1).get() or {}
        
        # 处理新记录
        new_banned_ips = set()
        max_id = last_id
        
        for key, record in new_records.items():
            ip = record.get('ip')
            record_id = record.get('id')
            if ip and ip not in banned_ips:
                if ban_ip(ip):
                    new_banned_ips.add(ip)
            if record_id:
                max_id = max(max_id, record_id)
        
        # 提交 newip 到 Firebase，确保 ID 递增
        new_id = max_id + 1
        timestamp = int(time.time())
        new_record = {
            'ip': newip,
            'id': new_id,
            'timestamp': timestamp
        }
        ref.push().set(new_record)
        
        # 更新配置和本地文件
        config["last_sync_id"] = new_id
        new_banned_ips.add(newip)
        if save_banned_ips(new_banned_ips):
            save_config(config)
            return True
        return False
        
    except Exception as e:
        logger.error(f"Error syncing IPs: {e}")
        return False

def ban_ip(ip):
    """封禁单个 IP"""
    try:
        subprocess.run(["fail2ban-client", "set", "sshd", "banip", ip],
                        check=True,
                        capture_output=True)
        logger.info(f"Banned IP: {ip}")
        return True
    except Exception as e:
        logger.error(f"Failed to ban IP {ip}: {e}")
    return False

def log_access(ip, error):
    """记录访问日志并处理可疑IP"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"{timestamp} - IP: {ip} - Error: {error}"
    logger.info(log_entry.strip())
    
    try:
        # 先确保本地安全
        if not ban_ip(ip):
            logger.warning(f"Warning: Failed to ban IP locally: {ip}")
            
        # 同步到云端，失败不影响本地安全
        if not sync_ips(ip):
            logger.warning(f"Warning: Failed to sync IP to cloud: {ip}")
            
    except Exception as e:
        logger.error(f"Critical error in log_access: {e}")


def handle_client(client_socket, client_address):
    """处理客户端连接"""
    ip = client_address[0]
    try:
        # 发送模拟的标准 SSH 欢迎消息
        client_socket.sendall(b"SSH-2.0-OpenSSH_8.6p1 Ubuntu-4ubuntu0.7\r\n")
        
        # 2. 接收客户端的协议标识
        client_data = client_socket.recv(1024).decode("utf-8").strip()

        # （这里可以简单化，不发送真实的密钥交换数据）
        client_socket.sendall(b"SSH-2.0-Server-Kex-Message\r\n")
        data = client_socket.recv(1024)
        client_socket.sendall(b"Password authentication failed\r\n")
        log_access(ip,client_data.split("\n")[0])

    except Exception as e:
        logger.error(f"Error handling client {client_address}: {e}")
    finally:
        client_socket.close()

def start_server():
    """启动模拟 SSH 服务"""
    init_firebase()
    global banned_ips
    cfg=load_config()
    HOST = cfg["network"]["host"]
    PORT = cfg["network"]["port"]
    banned_ips=load_banned_ips()
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST,PORT))
    server.listen(5)
    logger.info(f"Mock SSH server listening on {HOST}:{PORT}")

    try:
        while True:
            client_socket, client_address = server.accept()
            logger.info(f"Connection received from {client_address[0]}:{client_address[1]}")
            client_handler = threading.Thread(
                target=handle_client,
                args=(client_socket, client_address)
            )
            client_handler.start()
    except KeyboardInterrupt:
        logger.info("Shutting down server...")
    finally:
        server.close()

if __name__ == "__main__":
    start_server()