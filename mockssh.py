import socket
import threading
from datetime import datetime
import os
import traceback
import subprocess
import re

HOST = "0.0.0.0"  # 监听所有网络接口
PORT = 22       # 模拟 SSH 的端口
LOG_FILE = "ssh_baned_ip.txt"

def git_commit_and_push(file_path, commit_message="Update banned IP list"):
    """
    将文件提交到git仓库并推送到远程
    
    Args:
        file_path (str): 要提交的文件路径
        commit_message (str): 提交信息
        
    Returns:
        bool: 操作是否成功
        
    Raises:
        Exception: 当git操作失败时抛出，包含详细的错误信息
    """
    if not os.path.exists(file_path):
        raise Exception(f"File not found: {file_path}")
        
    try:
        # 添加文件到暂存区
        result = subprocess.run(["git", "add", file_path], 
                              check=True, 
                              capture_output=True, 
                              text=True)
        if result.stderr:
            raise Exception(f"Warning during git add: {result.stderr}")
            
        # 提交更改
        result = subprocess.run(["git", "commit", "-m", commit_message], 
                              check=True, 
                              capture_output=True, 
                              text=True)
        if result.stderr and "nothing to commit" not in result.stderr:
            raise Exception(f"Warning during git commit: {result.stderr}")
            
        # 推送到远程
        result = subprocess.run(["git", "push"], 
                              check=True, 
                              capture_output=True, 
                              text=True)
        if result.stderr and "Everything up-to-date" not in result.stderr:
            raise Exception(f"Warning during git push: {result.stderr}")
            
        print("Successfully committed and pushed changes to repository")
        return True
        
    except subprocess.CalledProcessError as e:
        error_msg = f"Git operation failed: {e.stderr if e.stderr else str(e)}"
        if e.cmd:
            error_msg += f"\nFailed command: {' '.join(e.cmd)}"
        print(error_msg)
        return False
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return False

def extract_ips_from_log(log_content):
    """从日志内容中提取所有 IP 地址"""
    ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
    return set(re.findall(ip_pattern, log_content))

def sync_and_compare_logs():
    """
    同步远程日志并比较差异
    
    Returns:
        set: 新增的 IP 地址集合
    """
    try:
        # 保存当前日志内容
        current_ips = set()
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, 'r') as f:
                current_ips = extract_ips_from_log(f.read())
        
        # 获取远程更新
        subprocess.run(["git", "fetch", "origin"], check=True, capture_output=True)
        subprocess.run(["git", "reset", "--hard", "origin/main"], check=True, capture_output=True)
        
        # 读取更新后的文件内容
        updated_ips = set()
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, 'r') as f:
                updated_ips = extract_ips_from_log(f.read())
        
        # 返回新增的 IP
        return updated_ips - current_ips
    except Exception as e:
        print(f"Error syncing logs: {str(e)}")
        return set()

def log_access(ip, error):
    """记录访问日志到文件"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {ip}: {error}\n"
    print(log_entry.strip())
    
    try:
        # 同步并检查新增 IP
        new_ips = sync_and_compare_logs()
        for new_ip in new_ips:
            try:
                subprocess.run(["fail2ban-client", "set", "sshd", "banip", new_ip], 
                             check=True, capture_output=True)
                print(f"Added new IP to fail2ban: {new_ip}")
            except subprocess.CalledProcessError as e:
                print(f"Failed to ban IP {new_ip}: {e.stderr}")
        
        # 追加新的日志条目
        with open(LOG_FILE, "a") as f:
            f.write(log_entry)
            
        # 提交并推送更改
        git_commit_and_push(LOG_FILE)
        
    except Exception as e:
        print(f"Error in log_access: {str(e)}")

def handle_client(client_socket, client_address):
    """处理客户端连接"""
    ip = client_address[0]
    try:
        # 发送模拟的标准 SSH 欢迎消息
        client_socket.sendall(b"SSH-2.0-OpenSSH_8.6p1 Ubuntu-4ubuntu0.7\r\n")
        
        # 2. 接收客户端的协议标识
        client_data = client_socket.recv(1024).decode("utf-8").strip()
        #print(f"Received from client: {client_data}")

        # （这里可以简单化，不发送真实的密钥交换数据）
        client_socket.sendall(b"SSH-2.0-Server-Kex-Message\r\n")
        data = client_socket.recv(1024)
        #print(data)
        client_socket.sendall(b"Password authentication failed\r\n")
        log_access(ip,client_data.split("\n")[0])


    except Exception as e:
        print(f"Error handling client {client_address}: {e}")
    finally:
        client_socket.close()

def start_server():
    """启动模拟 SSH 服务"""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(5)
    print(f"Mock SSH server listening on {HOST}:{PORT}")

    try:
        while True:
            client_socket, client_address = server.accept()
            print(f"Connection received from {client_address[0]}:{client_address[1]}")
            client_handler = threading.Thread(
                target=handle_client,
                args=(client_socket, client_address)
            )
            client_handler.start()
    except KeyboardInterrupt:
        print("Shutting down server...")
    finally:
        server.close()

if __name__ == "__main__":
    start_server()