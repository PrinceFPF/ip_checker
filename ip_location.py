#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
IP地址归属地识别工具
功能：
1. 下载最新的IPv4和IPv6地址库到本地
2. 批量识别IP地址归属地
3. 支持从Excel文件读取IP地址列表
4. 同时支持IPv4和IPv6地址
5. 使用纯真IP数据库优化中国IP地址识别
"""

import os
import sys
import requests
import tarfile
import pandas as pd
import ipaddress
from pathlib import Path
import geoip2.database
from geoip2.errors import AddressNotFoundError
import argparse
import ipdb
from tqdm import tqdm
from datetime import datetime

class IPLocationChecker:
    def __init__(self, license_key=None):
        """初始化IP地址库检查器"""
        self.license_key = license_key or os.getenv('MAXMIND_LICENSE_KEY')
        self.data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
        self.geolite2_dir = os.path.join(self.data_dir, 'GeoLite2')
        self.pureip_dir = os.path.join(self.data_dir, 'PureIPDB')
        
        # 数据库文件路径
        self.geolite2_db_path = os.path.join(self.geolite2_dir, 'GeoLite2-City.mmdb')
        self.pureip_file = os.path.join(self.pureip_dir, 'qqwry.ipdb')
        
        # 创建必要的目录
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.geolite2_dir, exist_ok=True)
        os.makedirs(self.pureip_dir, exist_ok=True)
        
        # 初始化数据库
        self._init_databases()
        
    def _init_databases(self):
        """初始化IP地址数据库"""
        # 初始化GeoLite2数据库
        self.geolite2_db = None
        self._init_geolite2()
        
        # 初始化PureIPDB数据库
        self.pureip_db = None
        self._init_pureip()
        
    def _init_pureip(self):
        """初始化PureIPDB数据库"""
        try:
            if os.path.exists(self.pureip_file):
                print("\n[信息] 正在加载 PureIPDB 数据库...")
                self.pureip_db = ipdb.City(self.pureip_file)
                print("[成功] PureIPDB 数据库加载完成")
                print(f"[信息] 支持的语言: {self.pureip_db.languages()}")
                print(f"[信息] 支持的字段: {self.pureip_db.fields()}")
                build_time = datetime.fromtimestamp(self.pureip_db.build_time())
                print(f"[信息] 数据库构建时间: {build_time.strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                print("[警告] PureIPDB 数据库文件不存在")
        except Exception as e:
            print(f"[错误] PureIPDB 数据库加载失败: {str(e)}")
            
    def query(self, ip):
        """查询IP地址的归属地信息"""
        try:
            # 验证IP地址格式
            ip_obj = ipaddress.ip_address(ip)
            is_ipv6 = isinstance(ip_obj, ipaddress.IPv6Address)
            
            # 优先使用PureIPDB数据库查询
            if self.pureip_db:
                try:
                    # 使用find_map方法获取字典格式的结果
                    result = self.pureip_db.find_map(ip, "CN")
                    if result and result.get('country_name') != '未知':
                        return {
                            'country': result.get('country_name', '未知'),
                            'region': result.get('region_name', '未知'),
                            'city': result.get('city_name', '未知'),
                            'latitude': result.get('latitude', 0),
                            'longitude': result.get('longitude', 0),
                            'timezone': result.get('timezone', '未知'),
                            'source': 'PureIPDB'
                        }
                except Exception as e:
                    pass  # 静默失败，尝试使用下一个数据源
            
            # 如果PureIPDB查询失败或结果未知，尝试使用GeoLite2数据库查询
            if self.geolite2_db:
                try:
                    response = self.geolite2_db.city(ip)
                    return {
                        'country': response.country.name or '未知',
                        'region': response.subdivisions.most_specific.name if response.subdivisions else '未知',
                        'city': response.city.name or '未知',
                        'latitude': response.location.latitude,
                        'longitude': response.location.longitude,
                        'timezone': response.location.time_zone or '未知',
                        'source': 'GeoLite2'
                    }
                except Exception as e:
                    pass  # 静默失败，返回未知结果
            
            return {
                'country': '未知',
                'region': '未知',
                'city': '未知',
                'latitude': 0,
                'longitude': 0,
                'timezone': '未知',
                'source': '未知'
            }
            
        except ValueError:
            return {
                'country': '错误',
                'region': '错误',
                'city': '错误',
                'latitude': 0,
                'longitude': 0,
                'timezone': '错误',
                'source': '错误',
                'error': '无效的IP地址格式'
            }
    
    def download_with_progress(self, url, file_path, desc, proxies=None, headers=None):
        """通用的下载函数，带进度条显示"""
        try:
            response = requests.get(url, stream=True, proxies=proxies, headers=headers)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            block_size = 8192
            
            with open(file_path, 'wb') as f, tqdm(
                desc=desc,
                total=total_size,
                unit='iB',
                unit_scale=True,
                unit_divisor=1024,
            ) as pbar:
                for data in response.iter_content(block_size):
                    size = f.write(data)
                    pbar.update(size)
            
            return True
        except Exception as e:
            print(f"\n[错误] 下载失败: {str(e)}")
            if os.path.exists(file_path):
                os.remove(file_path)
            return False
            
    def download_geolite2_database(self, license_key=None):
        """下载最新的GeoLite2 City数据库"""
        try:
            print("\n[信息] 准备下载 GeoLite2 City 数据库...")
            license_key = license_key or self.license_key
            if not license_key:
                print("[错误] 需要提供 MaxMind 许可证密钥")
                return False
            
            # 构建下载URL
            edition_id = "GeoLite2-City"
            url = f"https://download.maxmind.com/app/geoip_download?edition_id={edition_id}&license_key={license_key}&suffix=tar.gz"
            
            # 下载数据库文件
            temp_file = os.path.join(self.geolite2_dir, "temp.tar.gz")
            if not self.download_with_progress(url, temp_file, "下载 GeoLite2 数据库"):
                return False
            
            print("[信息] 正在解压数据库文件...")
            try:
                with tarfile.open(temp_file, 'r:gz') as tar:
                    for member in tar.getmembers():
                        if member.name.endswith('.mmdb'):
                            member.name = os.path.basename(member.name)
                            tar.extract(member, self.geolite2_dir)
                            extracted_file = os.path.join(self.geolite2_dir, member.name)
                            os.rename(extracted_file, self.geolite2_db_path)
                            break
                
                os.remove(temp_file)
                print("[成功] GeoLite2 数据库更新完成")
                return True
                
            except Exception as e:
                print(f"[错误] 解压数据库文件失败: {str(e)}")
                return False
                
        except Exception as e:
            print(f"[错误] 下载过程中发生异常: {str(e)}")
            return False
            
    def download_pureip_database(self):
        """下载最新的PureIPDB数据库"""
        try:
            print("\n[信息] 准备下载 PureIPDB 数据库...")
            
            url = "https://raw.gitmirror.com/nmgliangwei/qqwry.ipdb/main/qqwry.ipdb"
            
            # 使用固定的代理地址
            proxies = {
                'http': 'http://127.0.0.1:7890',
                'https': 'http://127.0.0.1:7890'
            }
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            temp_file = f"{self.pureip_file}.tmp"
            
            if not self.download_with_progress(url, temp_file, "下载 PureIPDB 数据库", proxies=proxies, headers=headers):
                return False
            
            # 验证文件
            print("[信息] 正在验证数据库文件...")
            file_size = os.path.getsize(temp_file)
            if file_size < 1024*1024:
                print("[错误] 下载的文件过小，可能不是有效的数据库文件")
                os.remove(temp_file)
                return False
            
            # 验证文件格式
            try:
                with open(temp_file, 'rb') as f:
                    header = f.read(4)
                    if len(header) == 4:
                        meta_length = int.from_bytes(header, byteorder='big')
                        if 0 < meta_length < 1024*1024:
                            if os.path.exists(self.pureip_file):
                                os.remove(self.pureip_file)
                            os.rename(temp_file, self.pureip_file)
                            print(f"[成功] PureIPDB 数据库更新完成 ({file_size/1024/1024:.2f} MB)")
                            return True
                        else:
                            print("[错误] 数据库文件格式无效")
                    else:
                        print("[错误] 无法读取文件头")
            except Exception as e:
                print(f"[错误] 验证文件时出错: {str(e)}")
            
            if os.path.exists(temp_file):
                os.remove(temp_file)
            return False
            
        except Exception as e:
            print(f"[错误] 下载过程中发生异常: {str(e)}")
            if os.path.exists(f"{self.pureip_file}.tmp"):
                os.remove(f"{self.pureip_file}.tmp")
            return False
    
    def process_excel_file(self, excel_path, output_path=None):
        """处理Excel文件中的IP地址"""
        try:
            print(f"\n[信息] 开始处理Excel文件: {excel_path}")
            
            # 读取Excel文件
            df = pd.read_excel(excel_path)
            print(f"[信息] 成功读取Excel文件，共有 {len(df)} 行数据")
            
            if len(df.columns) < 2:
                print("[错误] Excel文件格式错误：应该至少包含两列（序号和IP地址）")
                return False
            
            # 假设第一列是序号，第二列是IP地址
            ip_column = df.columns[1]
            
            # 创建新的DataFrame来存储结果
            result_df = pd.DataFrame()
            result_df['序号'] = df[df.columns[0]]  # 复制序号列
            result_df['IP地址'] = df[ip_column]    # 复制IP地址列
            result_df['国家'] = ''
            result_df['地区'] = ''
            result_df['城市'] = ''
            result_df['经度'] = pd.NA
            result_df['纬度'] = pd.NA
            result_df['时区'] = ''
            result_df['数据来源'] = ''
            result_df['错误'] = ''
            
            # 使用tqdm创建进度条
            print("[信息] 开始查询IP地址信息...")
            for idx in tqdm(range(len(df)), desc="处理进度", unit="条"):
                # 获取IP地址并确保格式正确
                ip = df.iloc[idx][ip_column]
                if pd.isna(ip) or ip == "":
                    result_df.at[idx, '错误'] = "IP地址为空"
                    continue
                
                # 对于IPv6地址，确保使用原始格式
                try:
                    ip_obj = ipaddress.ip_address(str(ip).strip())
                    ip = str(ip_obj)  # 使用标准化的IP地址格式
                except ValueError:
                    result_df.at[idx, '错误'] = "无效的IP地址格式"
                    continue
                
                result = self.query(ip)
                
                if "error" in result:
                    result_df.at[idx, '错误'] = result["error"]
                else:
                    result_df.at[idx, '国家'] = result["country"]
                    result_df.at[idx, '地区'] = result["region"]
                    result_df.at[idx, '城市'] = result["city"]
                    result_df.at[idx, '经度'] = result["longitude"]
                    result_df.at[idx, '纬度'] = result["latitude"]
                    result_df.at[idx, '时区'] = result["timezone"]
                    result_df.at[idx, '数据来源'] = result["source"]
            
            # 确定输出文件路径
            if output_path is None:
                excel_path = Path(excel_path)
                output_path = excel_path.parent / f"{excel_path.stem}_results{excel_path.suffix}"
            
            # 保存结果
            print("[信息] 正在保存查询结果...")
            try:
                # 将数值类型的列转换为字符串，避免编码问题
                result_df['经度'] = result_df['经度'].astype(str).replace('nan', '')
                result_df['纬度'] = result_df['纬度'].astype(str).replace('nan', '')
                
                # 使用xlsxwriter引擎保存
                with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
                    result_df.to_excel(writer, index=False, sheet_name='Sheet1')
                    
                    # 获取worksheet对象并设置列宽
                    worksheet = writer.sheets['Sheet1']
                    for idx, col in enumerate(result_df.columns):
                        max_length = max(
                            result_df[col].astype(str).apply(len).max(),
                            len(str(col))
                        )
                        worksheet.set_column(idx, idx, max_length + 2)
                
                print(f"[成功] 结果已保存到: {output_path}")
                return True
                
            except Exception as e:
                print(f"[错误] 保存Excel文件失败: {str(e)}")
                return False
            
        except Exception as e:
            print(f"[错误] 处理Excel文件时出错: {str(e)}")
            return False
    
    def close(self):
        """关闭数据库连接"""
        if self.geolite2_db:
            self.geolite2_db.close()
            self.geolite2_db = None
        # ipdb.City对象不需要关闭
        self.pureip_db = None

    def _init_geolite2(self):
        """初始化GeoLite2数据库"""
        try:
            if os.path.exists(self.geolite2_db_path):
                print("\n[信息] 正在加载 GeoLite2 数据库...")
                self.geolite2_db = geoip2.database.Reader(self.geolite2_db_path)
                print("[成功] GeoLite2 数据库加载完成")
            else:
                print("[警告] GeoLite2 数据库文件不存在")
        except Exception as e:
            print(f"[错误] GeoLite2 数据库加载失败: {str(e)}")
            self.geolite2_db = None


def main():
    """主函数"""
    try:
        parser = argparse.ArgumentParser(description="IP地址归属地识别工具")
        parser.add_argument("--download", action="store_true", help="下载IP地址库（如果不存在）")
        parser.add_argument("--update", action="store_true", help="强制更新IP地址库")
        parser.add_argument("--license-key", help="MaxMind许可证密钥")
        parser.add_argument("--ip", help="要查询的IP地址")
        parser.add_argument("--excel", help="要处理的Excel文件路径")
        parser.add_argument("--output", help="结果输出的Excel文件路径")
        
        args = parser.parse_args()
        
        # 创建IP地址检查器实例
        checker = IPLocationChecker(args.license_key)
        
        # 如果指定了下载或更新选项，下载数据库
        if args.download or args.update:
            if not args.license_key and not checker.license_key:
                print("[错误] 下载GeoLite2数据库需要提供MaxMind许可证密钥")
                print("[提示] 您可以通过以下方式提供许可证密钥：")
                print("       1. 使用--license-key参数")
                print("       2. 设置环境变量MAXMIND_LICENSE_KEY")
                return 1
            
            # 下载GeoLite2数据库
            if args.update or not os.path.exists(checker.geolite2_db_path):
                if args.update:
                    print("[信息] 正在更新GeoLite2数据库...")
                else:
                    print("[信息] 正在下载GeoLite2数据库...")
                    
                # 如果是更新模式且文件存在，先关闭数据库连接并删除旧文件
                if args.update and os.path.exists(checker.geolite2_db_path):
                    checker.close()
                    try:
                        os.remove(checker.geolite2_db_path)
                    except PermissionError:
                        print("[错误] 无法删除旧的数据库文件，请检查文件权限")
                        return 1
                    except Exception as e:
                        print(f"[错误] 删除旧数据库文件时出错: {str(e)}")
                        return 1
                    
                if not checker.download_geolite2_database(args.license_key):
                    print("[错误] GeoLite2数据库下载失败")
                    print("[提示] 请检查：")
                    print("       1. 网络连接是否正常")
                    print("       2. MaxMind许可证密钥是否有效")
                    print("       3. 磁盘空间是否充足")
                    return 1
            
            # 下载PureIPDB数据库
            if args.update or not os.path.exists(checker.pureip_file):
                if args.update:
                    print("[信息] 正在更新PureIPDB数据库...")
                else:
                    print("[信息] 正在下载PureIPDB数据库...")
                    
                # 如果是更新模式且文件存在，先关闭数据库连接并删除旧文件
                if args.update and os.path.exists(checker.pureip_file):
                    checker.close()
                    try:
                        os.remove(checker.pureip_file)
                    except PermissionError:
                        print("[错误] 无法删除旧的数据库文件，请检查文件权限")
                        return 1
                    except Exception as e:
                        print(f"[错误] 删除旧数据库文件时出错: {str(e)}")
                        return 1
                    
                if not checker.download_pureip_database():
                    print("[错误] PureIPDB数据库下载失败")
                    print("[提示] 请检查：")
                    print("       1. 网络连接是否正常")
                    print("       2. 代理服务器(127.0.0.1:7890)是否正常运行")
                    print("       3. 磁盘空间是否充足")
                    return 1
            
            if args.update:
                print("[成功] 数据库更新完成")
                # 重新初始化数据库
                checker._init_databases()
            else:
                print("[成功] 数据库下载完成")
            return 0
        
        # 如果指定了IP地址，查询单个IP
        if args.ip:
            try:
                result = checker.query(args.ip)
                print(f"\n[信息] IP地址: {args.ip}")
                print(f"[信息] 国家: {result['country']}")
                print(f"[信息] 地区: {result['region']}")
                print(f"[信息] 城市: {result['city']}")
                print(f"[信息] 经度: {result['longitude']}")
                print(f"[信息] 纬度: {result['latitude']}")
                print(f"[信息] 时区: {result['timezone']}")
                print(f"[信息] 数据来源: {result['source']}")
                if 'error' in result:
                    print(f"[错误] {result['error']}")
                return 0
            except Exception as e:
                print(f"[错误] 查询IP地址时出错: {str(e)}")
                print("[提示] 请检查IP地址格式是否正确")
                return 1
        
        # 如果指定了Excel文件，处理Excel文件
        if args.excel:
            if not os.path.exists(args.excel):
                print(f"[错误] 找不到Excel文件: {args.excel}")
                print("[提示] 请检查：")
                print("       1. 文件路径是否正确")
                print("       2. 文件是否存在")
                print("       3. 是否有权限访问该文件")
                return 1
            
            try:
                output_file = args.output or os.path.splitext(args.excel)[0] + "_results.xlsx"
                if checker.process_excel_file(args.excel, output_file):
                    print(f"[成功] 处理完成，结果已保存到: {output_file}")
                    return 0
                else:
                    print("[错误] Excel处理失败")
                    return 1
            except PermissionError:
                print("[错误] 无法访问或保存Excel文件，请检查文件权限")
                return 1
            except Exception as e:
                print(f"[错误] 处理Excel文件时出错: {str(e)}")
                print("[提示] 请检查：")
                print("       1. Excel文件格式是否正确")
                print("       2. 是否有足够的磁盘空间")
                print("       3. 是否有权限写入输出文件")
                return 1
        
        # 如果没有指定任何操作，显示帮助信息
        print("[提示] 请指定要执行的操作，使用 -h 或 --help 查看帮助信息")
        parser.print_help()
        return 1
        
    except KeyboardInterrupt:
        print("\n[信息] 程序被用户中断")
        return 1
    except Exception as e:
        print(f"\n[错误] 程序执行过程中发生未预期的错误: {str(e)}")
        print("[提示] 这可能是一个bug，请报告给开发者")
        return 1
    finally:
        # 确保在程序退出时关闭数据库连接
        if 'checker' in locals():
            checker.close()


if __name__ == "__main__":
    sys.exit(main()) 