from __future__ import print_function

import json
import requests
import netaddr

IPRANGE_URLS = {
    "goog": "https://www.gstatic.com/ipranges/goog.json",
    "cloud": "https://www.gstatic.com/ipranges/cloud.json",
}

def get_data(link):
    data = json.loads(requests.get(link).text)
    if data:
        # print("{} published: {}".format(link, data.get("creationTime")))
        cidrs = netaddr.IPSet()
        for e in data["prefixes"]:
            if "ipv4Prefix" in e:
                cidrs.add(e.get("ipv4Prefix"))
        return cidrs

def main():
    cidrs = {group: get_data(link) for group, link in IPRANGE_URLS.items()}
    if len(cidrs) != 2:
        raise ValueError("ERROR: Could process data from Google")
    with open('cidrs/raw/google_cidr.txt', 'w') as raw:
        for ip_range in (cidrs["goog"].union(cidrs["cloud"])).iter_cidrs():
            raw.write(f"{ip_range}\n")

if __name__ == "__main__":
    main()
