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
pip3 install -r requirements.txt
```

3. 配置 Firebase：
- 在 Firebase Console 创建新项目
- 下载服务账号密钥文件
- 将密钥文件重命名为 `firebase-adminsdk.json` 并放在项目根目录
- 在 Firebase Console 中启用 Realtime Database
- Firebase 规则配置
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

可以修改 `config.json` 中的以下参数：
- 监听端口（默认：22）
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
   - 所需的依赖是否已安装


2. 如果日志不显示，检查：
   - 日志文件权限
   - 磁盘空间
   - Python 进程状态

## 许可证

本项目采用 MIT 许可证。

MIT 开源许可协议

版权所有 (c) 2024 MockSSH

特此免费授予任何获得本软件副本和相关文档文件（下称"软件"）的人不受限制地处置该软件的权利，
包括不受限制地使用、复制、修改、合并、发布、分发、转授许可和/或出售该软件副本，
以及再授权被配发了本软件的人如上的权利，须在下列条件下：

上述版权声明和本许可声明应包含在该软件的所有副本或实质成分中。

本软件是"如此"提供的，没有任何形式的明示或暗示的保证，包括但不限于对适销性、特定用途的
适用性和不侵权的保证。在任何情况下，作者或版权持有人都不对任何索赔、损害或其他责任负责，
无论这些追责来自合同、侵权或其它行为中，还是产生于、源于或有关于本软件以及本软件的使用或
其它处置。

## 贡献

欢迎提交 Issues 和 Pull Requests！
