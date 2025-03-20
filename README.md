# IP地址归属地识别工具

这是一个用于批量识别IP地址归属地的Python工具。它可以识别IPv4和IPv6地址，并支持从Excel文件中批量读取IP地址进行处理。

## 功能特点

- 自动下载最新的MaxMind GeoLite2 IP地址库（支持IPv4和IPv6）
- 支持从Excel文件中批量读取IP地址
- 识别IP地址的国家、地区、城市、经纬度和时区信息
- 结果保存到Excel文件中，便于查看和分析
- 同时支持IPv4和IPv6地址

## 安装依赖

在使用前，需要安装必要的Python依赖包：

```bash
pip install -r requirements.txt
```

## 使用方法

### 1. 获取MaxMind许可证密钥

本工具使用MaxMind GeoLite2数据库，需要一个免费的许可证密钥。

1. 访问 [MaxMind官网](https://dev.maxmind.com/geoip/geoip2/geolite2/) 注册一个免费账户
2. 登录后，在"My License Key"页面获取您的许可证密钥

### 2. 设置环境变量（可选）

为了方便使用，您可以将MaxMind许可证密钥设置为环境变量：

```bash
export MAXMIND_LICENSE_KEY="你的许可证密钥"
```

### 3. 使用命令行接口

#### 下载IP地址库

```bash
python ip_location.py --download --license-key "你的许可证密钥"
```

如果已经设置了环境变量，可以省略`--license-key`参数：

```bash
python ip_location.py --download
```
#### 更新IP地址库
```bash
python ip_location.py --update
```

#### 查询单个IP地址

```bash
python ip_location.py --ip "8.8.8.8"
```

#### 处理Excel文件中的IP地址

```bash
python ip_location.py --excel "example_ips.xlsx" --output "results.xlsx"
```

如果不指定输出文件，结果将保存在与输入文件相同的目录下，文件名为`输入文件名_results.xlsx`。

### 4. 创建示例IP地址Excel文件

本工具附带了一个脚本，可以生成一个包含示例IP地址的Excel文件，用于测试：

```bash
python example_ips.py
```

这将在当前目录下创建一个`example_ips.xlsx`文件，其中包含一些示例IPv4和IPv6地址。

## Excel文件格式

本工具期望输入的Excel文件具有以下格式：
- 第一列：序号
- 第二列：IP地址

输出Excel文件将包含以下列：
- 原始的序号和IP地址列
- 国家
- 地区
- 城市
- 经度
- 纬度
- 时区
- 错误（如有）

## 注意事项

1. geoip2IP地址库数据由MaxMind提供，精确度可能会有所不同
2. 本程序优先通过纯真IP地址库进行检索
3. 纯真IP地址库下载需要乘坐火箭，请现在程序中配置好代理
4. 使用批量处理大量IP地址时，处理速度取决于计算机性能

## 故障排除

如果遇到问题，请检查：

1. 是否正确安装了所有依赖包
2. 是否提供了有效的MaxMind许可证密钥
3. 输入的Excel文件格式是否正确
4. 是否有足够的硬盘空间用于存储IP地址库

## 许可证

本工具遵循MIT许可证发布。

使用的GeoLite2数据库由MaxMind创建，可从[https://www.maxmind.com](https://www.maxmind.com)获得。 
