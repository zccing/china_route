import ipaddress
import re
import math
import requests


IPRANGE_URLS = {'github': ['https://raw.githubusercontent.com/17mon/china_ip_list/master/china_ip_list.txt',
                          'https://github.com/misakaio/chnroutes2/raw/refs/heads/master/chnroutes.txt'
                          'https://metowolf.github.io/iplist/data/special/china.txt',
                          'https://github.com/zhufengme/block_cn_files/raw/refs/heads/master/cn_ip_list.txt',
                          'https://github.com/gaoyifan/china-operator-ip/raw/refs/heads/ip-lists/china.txt']
                'apnic': ['https://ftp.apnic.net/apnic/stats/apnic/delegated-apnic-latest', 
                          'https://ftp.apnic.net/apnic/stats/apnic/delegated-apnic-extended-latest',
                          'https://ftp.apnic.net/stats/ripe-ncc/delegated-ripencc-extended-latest',
                          'https://ftp.apnic.net/stats/ripe-ncc/delegated-ripencc-latest']}


def fetch_apnic_data():
    print("Fetching data from apnic.net, it might take a few minutes, please wait...")
    apnic_data = ''
    for url in IPRANGE_URLS.get('apnic'):
        apnic_data += requests.get(url).text
    cnregex = re.compile(
        r'apnic\|cn\|ipv4\|[0-9\.]+\|[0-9]+\|[0-9]+\|a.*', re.IGNORECASE)
    cndata = cnregex.findall(apnic_data)
    results = []
    for item in cndata:
        unit_items = item.split('|')
        starting_ip = unit_items[3]
        num_ip = int(unit_items[4])
        mask2 = 32-int(math.log(num_ip, 2))
        results.append(ipaddress.ip_network(f"{starting_ip}/{mask2}"))
    return results


def fetch_github_data():
    github_cn = requests.get(IPRANGE_URLS.get('github'))
    ipip_cidrs = []
    for url in github_cn:
      for cidr in url.text.split():
          ipip_cidrs.append(ipaddress.ip_network(cidr))
    return ipip_cidrs


def get_data(link):
    # 获取apnic的数据
    apnic_cidrs = fetch_apnic_data()
    # 获取ipip.net的开源数据
    ipip_cidrs = fetch_github_data()
    # 汇总合并
    cidrs = apnic_cidrs + ipip_cidrs
    summarized_networks = ipaddress.collapse_addresses(cidrs)
    return summarized_networks


def main():
    cidrs = get_data(IPRANGE_URLS)
    raw = open(r'cidrs/raw/china_cidr.txt', 'w+')
    mikrotik_route = open(r'cidrs/mikrotik/china_route.txt', 'w+')
    for ip_network in cidrs:
        ip_network = str(ip_network)
        # 保存纯网段
        raw.write(f"{ip_network}\n")
        # 保存成RouteOS脚本
        mikrotik_route.write(
            f"/ip route add distance=20 dst-address={ip_network} gateway=$iknowtheGW comment=China_Route;\n")
    raw.close()
    mikrotik_route.close()


if __name__ == "__main__":
    main()
