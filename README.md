# Mock SSH Server

一个用于模拟 SSH 服务的轻量级服务器，可以用来捕获潜在的恶意 SSH 登录尝试，并自动使用 fail2ban 进行 IP 封禁。

## 功能特点

- 模拟 SSH 服务器
- 自动记录登录尝试
- 与 fail2ban 集成
- Firebase 实时数据同步
- 自动 IP 封禁
- 日志记录

## 系统要求

- Python 3.x
- fail2ban
- Firebase Admin SDK
- 操作系统：macOS/Linux

## 安装步骤

1. 克隆仓库：
```bash
git clone https://github.com/dominolu/mockssh.git
cd mockssh
```

2. 安装依赖：
```bash
pip3 install firebase-admin
```

3. 配置 Firebase：
- 在 Firebase Console 创建新项目
- 下载服务账号密钥文件
- 将密钥文件重命名为 `firebase-adminsdk.json` 并放在项目根目录
- 在 Firebase Console 中启用 Realtime Database



### Firebase 规则配置

在 Firebase Console 中添加以下数据库规则：

```json
{
  "rules": {
    "banned_ips": {
      ".indexOn": ["id"]
    }
  }
}
```
4. 配置 fail2ban：
```bash
sudo apt-get install fail2ban  # Ubuntu/Debian
# 或
brew install fail2ban  # macOS
```


## 使用方法
### 先将系统的 ssh 端口 22 修改为其他端口以防冲突，也可在配置文件中模拟其他端口如 3389
### 启动服务

使用管理脚本启动服务：

```bash
# 添加执行权限
chmod +x mockssh.sh

# 启动服务
./mockssh.sh start

# 停止服务
./mockssh.sh stop

# 重启服务
./mockssh.sh restart

# 查看状态
./mockssh.sh status
```

### 查看日志

日志文件位置：`mockssh.log`

查看实时日志：
```bash
tail -f mockssh.log
```



### 自定义配置

可以修改 `mockssh.py` 中的以下参数：
- 监听端口（默认：22）
- 日志文件路径
- Firebase 配置路径

## 注意事项

1. 确保以 root 权限运行（需要访问系统端口）
2. 确保 fail2ban 服务正在运行
3. 保护好 Firebase 凭证文件
4. 定期检查日志文件大小

## 故障排除

1. 如果服务无法启动，检查：
   - 端口是否被占用
   - Firebase 配置是否正确
   - fail2ban 服务是否运行

2. 如果日志不显示，检查：
   - 日志文件权限
   - 磁盘空间
   - Python 进程状态

## 许可证

[选择合适的许可证]

## 贡献

欢迎提交 Issues 和 Pull Requests！
