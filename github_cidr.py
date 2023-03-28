import ipaddress
import json
import requests


IPRANGE_URLS = 'https://api.github.com/meta'

def get_data(link):
    """
    Gets JSON data from a specified link and processes it, returning a merged list of IP address ranges
    
    Args:
    link -- the link to retrieve data from
    
    Returns:
    A merged list of IP address ranges (List[str])
    """
    data = json.loads(requests.get(link).text)  # Retrieves content from the provided link, parses it using the json library into dictionary form
    data.pop('verifiable_password_authentication')  # Deletes the value associated with the key 'verifiable_password_authentication'
    cidrs = [ipaddress.ip_network(ip) for value in data.values()  # Iterates over the values in the dictionary
             for ip in value if is_valid_ipv4(ip)]  # Converts valid IP addresses to network address objects (ip_network) and saves them to a list
    summarized_cidrs = [str(network)  # Iterates over the network address object list, converting each object to string form
                        for network in ipaddress.collapse_addresses(cidrs)]
    return summarized_cidrs  # Returns the merged list of IP address ranges


def is_valid_ipv4(ip):
    """
    Determines if the given IP address is a valid IPv4 address.

    Args:
        ip: A string representing an IP address.

    Returns:
      A boolean indicating whether the given IP address is a valid IPv4 address.
    """
    try:
        ip_network = ipaddress.ip_network(ip)  # Create an IP network object from input IP address
        return ip_network.version == 4         # Return True if IP network version is 4, otherwise False
    except ValueError:
        return False                           # Return False if an exception is caught, indicating invalid input




def main():
    with open('cidrs/raw/github_cidr.txt', 'w') as raw:
        for ip_range in get_data(IPRANGE_URLS):
            raw.write(f'{ip_range}\n')


if __name__ == '__main__':
    main()
