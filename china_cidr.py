import ipaddress
import re
import math
import requests


IPRANGE_URLS = {'ipip.net': 'https://raw.githubusercontent.com/17mon/china_ip_list/master/china_ip_list.txt',
                'apnic': 'https://ftp.apnic.net/apnic/stats/apnic/delegated-apnic-latest'}


def fetch_apnic_data():
    print("Fetching data from apnic.net, it might take a few minutes, please wait...")
    data = requests.get(IPRANGE_URLS.get('apnic')).text
    cnregex = re.compile(
        r'apnic\|cn\|ipv4\|[0-9\.]+\|[0-9]+\|[0-9]+\|a.*', re.IGNORECASE)
    cndata = cnregex.findall(data)
    results = []
    for item in cndata:
        unit_items = item.split('|')
        starting_ip = unit_items[3]
        num_ip = int(unit_items[4])
        mask2 = 32-int(math.log(num_ip, 2))
        results.append(ipaddress.ip_network(f"{starting_ip}/{mask2}"))
    return results


def fetch_ipip_data():
    data = requests.get(IPRANGE_URLS.get('ipip.net')).text
    ipip_cidrs = []
    for cidr in data.split():
        ipip_cidrs.append(ipaddress.ip_network(cidr))
    return ipip_cidrs


def get_data(link):
    # 获取apnic的数据
    apnic_cidrs = fetch_apnic_data()
    # 获取ipip.net的开源数据
    ipip_cidrs = fetch_ipip_data()
    # 汇总合并
    cidrs = apnic_cidrs + ipip_cidrs
    summarized_networks = ipaddress.collapse_addresses(cidrs)
    return summarized_networks


def main():
    cidrs = get_data(IPRANGE_URLS)
    with open(r'cidrs/china_route.txt', 'w') as f:
        for ip in cidrs:
            f.write(f"{str(ip)}\n")


if __name__ == "__main__":
    main()
