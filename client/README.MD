FTP 系统 客户端
---
## 程序文件结构
+ server
    + bin
        + server_run.py  --> 客户端运行程序
    + core
        + __init__.py
        + server_main.py  --> 客户端主体代码
        + server_management.py  --> 客户端管理代码
    + local  --> 本地文件夹，上传下载内容都从这里起止
    + README.MD  --> 说明文档
---
## 程序实现功能
首页：
+ 选择server以及port进行连接，合法性检验
+ 文件的从local文件夹上传的服务端自己的home目录下
+ 文件从服务端自己选择的目录下载内容到local文件夹中国呢
+ 显示当前目录所有文件
+ 在当前目录下创建文件夹，删除文件及文件夹
+ 随意切换所在目录
+ 启动若存在因为服务端断开产生的断点文件，匹配并进行自动续传
+ 退出程序

## 程序的启动方式
+ 通过终端启动bin/client_run.py文件
---
## 登陆用户信息
+ 程序直接启动无需登陆
    + 客户端暂设置server:127.0.0.1; port: 9295
    + 可用用户Roger，密码qwe123登陆
    + 可用用户Jiang, 密码qwe123登陆（可以在客户端创建新用户）
---
## 程序运行效果
![client](https://i.loli.net/2020/05/10/794SVyjXMgmzbcF.jpg)---
## 程序运行流程图
![client_flowchart](https://i.loli.net/2020/05/10/RknGNB3lomcJYZf.png)