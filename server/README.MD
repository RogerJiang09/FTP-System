FTP 系统 服务端
---
## 程序文件结构
+ server
    + bin
        + server_run.py  --> 服务端运行程序
    + conf
        + __init__.py
        + accounts.ini  --> 用户信息储存文件
        + settings.py   --> 服务端设置信息
    + core
        + __init__.py
        + server_main.py  --> 服务端主体代码
        + server_management.py  --> 服务端管理代码
    + home
        + Jiang  --> 创建的用户文件夹（可删除）
        + Roger  --> 创建的用户文件夹（可删除）
    + README.MD  --> 说明文档
---
## 程序实现功能
首页：
+ 创建新用户，确定客户可用容量
+ 客户加密密码储存
+ 启动服务端程序，等待客户接入
+ 与客户端交互进行文件操作
+ 启动若存在因为服务端断开产生的断点文件，匹配并进行自动续传
+ 交互信息提示
+ 退出程序

## 程序的启动方式
+ 通过终端或python解释器启动bin/server_run.py文件
---
## 登陆用户信息
+ 程序直接启动无需登陆

---
## 程序运行效果
![server](https://i.loli.net/2020/05/10/s1kY4mRzcHpLdoT.jpg)
---
## 程序运行流程图
![server_flowchart](https://i.loli.net/2020/05/10/vFSg9p7AuBYy8t2.jpg)
