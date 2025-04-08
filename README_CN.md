# 简易的AI智能体
## 功能介绍
这个AI智能体可以进行任务自动分解，分步解决，浏览器搜索，以及文件生成功能。 

网络搜索功能以及文件生成功能主要借助的是MCP(Model Context Protocol)技术。 

作为一个老板，你可以给AI智能体一个任务。AI智能体会自动将任务分解成多个步骤，然后分步执行。如果，步骤中涉及到超越LLM能力范围的任务，LLM会通过MCP客户端向，MCP服务器发送请求，MCP服务器会选择合适的工具并返回结果。    

目前，已经完成的功能包括：浏览器搜索、markdown文件生成、文件上传功能。后期会继续补充终端控制、代码编写和执行、浏览器控制等功能。

## 快速使用
1. 克隆项目。
```
git clone https://github.com/Succoney/Simple-AI-Agent.git
cd Simple-AI-Agent/
```

2. 安装环境
```
conda create -n simple-agent python=3.12
conda activate simple-agent
```

3. 下载依赖
```
pip install -r requirements.txt

##如果安装失败的话，可以使用如下指令

python -m pip install -r requirements.txt
```

4. 配置大模型以及网页搜索的接口参数
在./config/config.env中输入相应的参数，包括模型名、访问地址、api-key以及网页搜索的接口以及api-key。

5. 启动AI智能体
```
cd agent/
sh run_agent.sh
```


## 功能演示
<iframe src="https://www.bilibili.com/video/BV1d5dJY8E4n?t=10.3" 
scrolling="no" border="0" frameborder="no" framespacing="0" 
allowfullscreen="true" width="560" height="315"> </iframe>
