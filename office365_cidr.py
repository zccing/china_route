import json
import ipaddress
import requests
import uuid

WS = "https://endpoints.office.com"
clientRequestId = str(uuid.uuid4())
session = requests.Session()

def webApiGet(methodName, instanceName):
    requestPath = f'{WS}/{methodName}/{instanceName}'
    response = session.get(requestPath, params={'clientRequestId': clientRequestId})
    return json.loads(response.text)

def get_cidrs(instanceNames: list) -> list:
    cidrs = [ipaddress.ip_network(ip_network) for instanceName in instanceNames for endpointSet in webApiGet('endpoints', instanceName) for ip_network in endpointSet.get('ips', []) if ipaddress.ip_network(ip_network).version == 4]
    return [str(network) for network in ipaddress.collapse_addresses(cidrs)]

def main():
    instances = [office365_area['instance'] for office365_area in webApiGet('version', '')]
    print(instances)
    with open('cidrs/raw/office365_china_cidr.txt', 'w') as raw_china, \
            open('cidrs/mikrotik/office365_china_route.txt', 'w') as mikrotik_china, \
                open('cidrs/raw/office365_other_cidr.txt', 'w') as raw_other:
        for china_network in get_cidrs(['China']):
            raw_china.write(f"{china_network}\n")
            mikrotik_china.write(
                f"/ip route add distance=20 dst-address={china_network} gateway=$iknowtheGW comment=China_Route_office365;\n")
        instances.remove('China')
        for other_network in get_cidrs(instances):
            raw_other.write(f"{other_network}\n")

if __name__ == '__main__':
    main()
