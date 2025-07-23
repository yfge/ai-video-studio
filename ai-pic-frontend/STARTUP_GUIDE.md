# 启动指南

## 🚀 快速启动

### 1. 确保在正确的目录
```bash
cd ai-pic-frontend
```

### 2. 安装依赖（如果还没安装）
```bash
npm install
```

### 3. 启动开发服务器
```bash
npm run dev
```

### 4. 访问应用
打开浏览器访问 [http://localhost:3000](http://localhost:3000)

## 🔧 故障排除

### 问题1: 路径错误
**错误信息**: `npm error enoent Could not read package.json`

**解决方案**: 确保你在 `ai-pic-frontend` 目录下运行命令，而不是在父目录 `ai-pic` 下。

### 问题2: Turbopack 路径问题
**错误信息**: `Cannot depend on path outside of root directory`

**解决方案**: 
- 使用默认的 `npm run dev` 命令（不使用 Turbopack）
- 如果需要使用 Turbopack，运行 `npm run dev:turbo`

### 问题3: 端口被占用
**错误信息**: `Port 3000 is already in use`

**解决方案**:
```bash
# 查找占用端口的进程
netstat -ano | findstr :3000

# 终止进程（替换 PID 为实际的进程ID）
taskkill /PID <PID> /F
```

## 📱 测试页面

启动成功后，你可以访问以下页面：

- **首页**: http://localhost:3000
- **登录页面**: http://localhost:3000/login
- **注册页面**: http://localhost:3000/register
- **任务管理**: http://localhost:3000/tasks
- **图片画廊**: http://localhost:3000/gallery

## 🛠️ 开发命令

```bash
# 开发模式（推荐）
npm run dev

# 开发模式（使用 Turbopack）
npm run dev:turbo

# 构建生产版本
npm run build

# 启动生产服务器
npm start

# 代码检查
npm run lint
```

## 📝 注意事项

1. **目录结构**: 确保在 `ai-pic-frontend` 目录下运行命令
2. **Node.js 版本**: 需要 Node.js 18+ 版本
3. **网络连接**: 首次安装依赖需要网络连接
4. **端口冲突**: 如果3000端口被占用，Next.js会自动使用下一个可用端口

## 🆘 获取帮助

如果遇到其他问题，请检查：
1. Node.js 版本是否正确
2. 是否在正确的目录下
3. 依赖是否正确安装
4. 端口是否被其他程序占用 