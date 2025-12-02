import ipaddress
import re
import math
import os

import requests

# IP 数据源 URL 列表
IPRANGE_URLS = {
    'github': [
        'https://raw.githubusercontent.com/17mon/china_ip_list/master/china_ip_list.txt',
        'https://github.com/misakaio/chnroutes2/raw/refs/heads/master/chnroutes.txt',
        'https://metowolf.github.io/iplist/data/special/china.txt',
        'https://github.com/zhufengme/block_cn_files/raw/refs/heads/master/cn_ip_list.txt',
        'https://github.com/gaoyifan/china-operator-ip/raw/refs/heads/ip-lists/china.txt'
    ],
    'apnic': [
        'https://ftp.apnic.net/apnic/stats/apnic/delegated-apnic-latest',
        'https://ftp.apnic.net/apnic/stats/apnic/delegated-apnic-extended-latest',
        'https://ftp.apnic.net/stats/ripe-ncc/delegated-ripencc-extended-latest',
        'https://ftp.apnic.net/stats/ripe-ncc/delegated-ripencc-latest'
    ]
}

# 中国 IP 正则匹配
CN_IP_REGEX = re.compile(r'apnic\|cn\|ipv4\|([0-9.]+)\|(\d+)\|', re.IGNORECASE)

# 输出文件路径
RAW_OUTPUT = 'cidrs/raw/china_cidr.txt'
MIKROTIK_OUTPUT = 'cidrs/mikrotik/china_route.txt'
IPSET_OUTPUT = 'cidrs/ipset/china_ipset.txt'


def get_proxies() -> dict | None:
    """从环境变量获取代理配置"""
    http_proxy = os.environ.get('HTTP_PROXY') or os.environ.get('http_proxy')
    https_proxy = os.environ.get('HTTPS_PROXY') or os.environ.get('https_proxy')
    
    if http_proxy or https_proxy:
        proxies = {}
        if http_proxy:
            proxies['http'] = http_proxy
        if https_proxy:
            proxies['https'] = https_proxy
        print(f"使用代理: {proxies}")
        return proxies
    return None


def fetch_url(url: str, proxies: dict | None = None, timeout: int = 30) -> str:
    """获取 URL 内容，支持代理和超时"""
    try:
        response = requests.get(url, proxies=proxies, timeout=timeout)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"获取 {url} 失败: {e}")
        return ''


def fetch_apnic_data(proxies: dict | None = None) -> list[ipaddress.IPv4Network]:
    """从 APNIC 获取中国 IP 数据"""
    print("正在从 APNIC 获取数据，可能需要几分钟，请稍候...")
    
    results = []
    for url in IPRANGE_URLS.get('apnic', []):
        print(f"  获取: {url}")
        data = fetch_url(url, proxies)
        
        for match in CN_IP_REGEX.finditer(data):
            starting_ip = match.group(1)
            num_ip = int(match.group(2))
            mask = 32 - int(math.log2(num_ip))
            try:
                results.append(ipaddress.ip_network(f"{starting_ip}/{mask}"))
            except ValueError as e:
                print(f"  无效的 IP 网络: {starting_ip}/{mask} - {e}")
    
    print(f"  从 APNIC 获取到 {len(results)} 条记录")
    return results


def fetch_github_data(proxies: dict | None = None) -> list[ipaddress.IPv4Network]:
    """从 GitHub 数据源获取中国 IP 数据"""
    print("正在从 GitHub 获取数据...")
    
    results = []
    for url in IPRANGE_URLS.get('github', []):
        print(f"  获取: {url}")
        data = fetch_url(url, proxies)
        
        for line in data.splitlines():
            line = line.strip()
            if line and not line.startswith('#'):
                try:
                    results.append(ipaddress.ip_network(line))
                except ValueError:
                    continue
    
    print(f"  从 GitHub 获取到 {len(results)} 条记录")
    return results


def get_china_cidrs() -> list[ipaddress.IPv4Network]:
    """获取并合并所有中国 IP 数据"""
    proxies = get_proxies()
    
    # 获取所有数据源
    apnic_cidrs = fetch_apnic_data(proxies)
    github_cidrs = fetch_github_data(proxies)
    
    # 汇总合并
    all_cidrs = apnic_cidrs + github_cidrs
    print(f"合并前共 {len(all_cidrs)} 条记录")
    
    # 合并重叠的网段
    summarized = list(ipaddress.collapse_addresses(all_cidrs))
    print(f"合并后共 {len(summarized)} 条记录")
    
    return summarized


def save_results(cidrs: list[ipaddress.IPv4Network]) -> None:
    """保存结果到文件"""
    # 确保输出目录存在
    os.makedirs(os.path.dirname(MIKROTIK_OUTPUT), exist_ok=True)
    os.makedirs(os.path.dirname(RAW_OUTPUT), exist_ok=True)
    
    with open(RAW_OUTPUT, 'w', encoding='utf-8') as raw_file, \
         open(MIKROTIK_OUTPUT, 'w', encoding='utf-8') as mikrotik_file:
        
        for network in cidrs:
            network_str = str(network)
            # 保存纯网段
            raw_file.write(f"{network_str}\n")
            # 保存成 RouterOS 脚本
            mikrotik_file.write(
                f"/ip route add distance=20 dst-address={network_str} "
                f"gateway=$iknowtheGW comment=China_Route;\n"
            )
    
    print(f"结果已保存到 {RAW_OUTPUT} 和 {MIKROTIK_OUTPUT}")


def main():
    """主函数"""
    cidrs = get_china_cidrs()
    save_results(cidrs)


if __name__ == "__main__":
    main()
