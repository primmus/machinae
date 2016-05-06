import collections
import re
import socket
from urllib.parse import urlparse


TargetInfo = collections.namedtuple("TargetInfo", ("target", "otype", "otype_detected"))
ErrorResult = collections.namedtuple("ErrorResult", ("target_info", "site_info", "error_info"))
ResultSet = collections.namedtuple("ResultSet", ("target_info", "results"))
SiteResults = collections.namedtuple("SiteResults", ("site_info", "resultset"))
Result = collections.namedtuple("Result", ("value", "pretty_name"))


def get_related_targets(target, otype=None):
    if otype is None:
        otype = get_target_type(target)

    targets = list()
    if otype == "url":
        u = urlparse(target)
        hostname_otype = get_target_type(u.hostname)
        targets.append((u.hostname, hostname_otype))
        for related in get_related_targets(u.hostname, hostname_otype):
            targets.append(related)
    elif otype == "email":
        (_, domain) = target.split("@", 1)
        domain_otype = get_target_type(domain)  # Wonder if this is necessary
        targets.append((domain, domain_otype))
        for related in get_related_targets(domain, domain_otype):
            targets.append(related)
    elif otype == "fqdn":
        for addr in socket.gethostbyname_ex(target)[2]:
            addr_otype = get_target_type(addr)  # Wonder if this is necessary
            targets.append((addr, addr_otype))
            for related in get_related_targets(addr, addr_otype):
                targets.append(related)
    return targets


def get_target_type(target):
    # IPv4
    try:
        socket.inet_aton(target)
    except:
        pass
    else:
        return "ipv4"

    # IPv6
    try:
        socket.inet_pton(socket.AF_INET6, target)
    except:
        pass
    else:
        return "ipv6"

    # Hashes
    if re.match("^[a-f0-9]{32}$", target, re.I):
        # MD5
        return "hash"
    elif re.match("^[a-f0-9]{40}$", target, re.I):
        # SHA-1
        return "hash.sha1"
    elif re.match("^[a-f0-9]{64}$", target, re.I):
        # SHA-256
        return "hash.sha256"
    elif re.match("^[a-f0-9]{128}$", target, re.I):
        # SHA-512
        return "hash.sha512"

    # URL
    elif re.match("^https?://", target, re.I):
        return "url"

    # Email Addresses
    elif re.match("^.*?@.*?$", target, re.I):
        return "email"

    # SSL fingerprints
    elif re.match("^(?:[a-f0-9]{2}:){19}[a-f0-9]{2}$", target, flags=re.I):
        return "sslfp"

    return "fqdn"


# d2 takes precedence
def dict_merge(d1, d2):
    d3 = d1.copy()
    for key in d2:
        if key in d3 and hasattr(d3[key], "items") and hasattr(d2[key], "items"):
            d3[key] = dict_merge(d3[key], d2[key])
        elif hasattr(d2[key], "items"):
            d3[key] = d2[key].copy()
        else:
            d3[key] = d2[key]
    return d3
