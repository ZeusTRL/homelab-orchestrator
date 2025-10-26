from ipaddress import ip_network


def no_overlaps(cidr_list: list[str]) -> bool:
    nets = [ip_network(c, strict=False) for c in cidr_list]
    for i, n1 in enumerate(nets):
        for n2 in nets[i+1:]:
            if n1.overlaps(n2):
                return False
    return True