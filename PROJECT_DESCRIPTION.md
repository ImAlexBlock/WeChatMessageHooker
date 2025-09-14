# WeChatMessages 项目说明

## 项目概述

WeChatMessages 是一个基于 [WeChatFerry](https://github.com/lich0821/WeChatFerry) 修改的微信 Hook 程序，专门用于实时接收微信消息。该项目仅能接收消息，无法进行其他操作，仅供学习参考和技术研究使用。

**注意：本程序仅支持微信 Windows 版 `3.9.12.17`。**

## 项目结构

```
WeChatMessages/
├── common/           # 通用工具和日志模块
├── injector/         # DLL 注入器
├── libs/             # 第三方库文件（如 libcurl）
├── spy/              # 消息监听和处理模块
├── README.md         # 项目说明文件
└── WeChatMessages.sln # Visual Studio 解决方案文件
```

### 各模块详细说明

#### 1. common 模块

包含项目的通用工具函数和日志系统：

- `log.h/log.cpp`: 基于 spdlog 的日志系统实现，支持文件滚动记录
- `util.h/util.cpp`: 提供各种实用工具函数，包括：
  - 微信进程查找和版本检测
  - 字符串编码转换（UTF-8、GB2312、宽字符等）
  - 内存读取和解析微信内部数据结构

#### 2. injector 模块

负责将 spy.dll 注入到微信进程中的注入器：

- `injector.h/injector.cpp`: 实现 DLL 注入功能，主要函数包括：
  - `InjectDll`: 将指定 DLL 注入到目标进程
  - `EjectDll`: 从目标进程卸载 DLL
  - `CallDllFunc`: 调用注入 DLL 中的指定函数

#### 3. spy 模块

核心的消息监听和处理模块：

- `spy.h/spy.cpp`: 模块初始化和清理函数
- `receive_msg.h/receive_msg.cpp`: 消息接收和处理的核心实现
- `spy_types.h`: 定义微信相关的数据结构

关键功能：
- 使用 MinHook 库 Hook 微信的消息接收函数
- 解析微信消息的各种属性（内容、发送者、时间等）
- 将消息通过 HTTP POST 请求发送到指定服务器

#### 4. libs 模块

包含项目依赖的第三方库：

- `libcurl`: 用于发送 HTTP 请求
- `spdlog`: 用于日志记录
- `MinHook`: 用于函数 Hook

## 工作原理

1. **微信进程检测**: 程序首先检测系统中是否已运行微信，如果没有则启动微信。

2. **DLL 注入**: 使用 injector 模块将 spy.dll 注入到微信进程中。

3. **模块初始化**: spy.dll 被加载后，执行初始化函数：
   - 检查微信版本是否匹配（仅支持 3.9.12.17）
   - 初始化日志系统
   - 获取 WeChatWin.dll 模块地址

4. **消息 Hook**: 
   - 通过 MinHook 库 Hook 微信的消息接收函数（位于 WeChatWin.dll 的特定偏移地址）
   - 当微信接收到新消息时，会调用被 Hook 的函数

5. **消息解析**: 
   - 在 Hook 回调函数中解析消息内容
   - 提取消息的各种属性（ID、类型、内容、发送者等）

6. **消息转发**: 
   - 将解析后的消息封装成 JSON 格式
   - 通过 libcurl 发送 HTTP POST 请求到指定的服务器地址

## 消息类型支持

项目支持多种微信消息类型，包括但不限于：
- 文字消息
- 图片消息
- 语音消息
- 视频消息
- 文件消息
- 位置消息
- 链接消息
- 红包消息
- 系统通知等

## 使用说明

1. 确保安装了微信 Windows 版本 3.9.12.17
2. 编译整个解决方案
3. 运行 injector 程序，它会自动注入 spy.dll 到微信进程中
4. 配置接收消息的服务器地址
5. 微信接收到的消息会自动转发到指定服务器

## 注意事项

- 本项目仅供学习和技术研究使用，请勿用于非法用途
- 仅支持特定版本的微信（3.9.12.17），其他版本可能无法正常工作
- 使用前请确保了解相关法律法规，避免侵犯他人隐私

## 技术细节

- 使用 MinHook 进行函数 Hook
- 使用 libcurl 发送 HTTP 请求
- 使用 spdlog 进行日志记录
- 支持 Unicode 和多字节字符集转换
- 通过 Windows API 实现 DLL 注入

更多技术细节和实现原理，请参考作者的[博客](https://producer.mrxiaom.top/post/wechat-message-hook/)。