#!/usr/bin/python3

import sys
from cli_client import ApiClient, Path
from rpipe_utils import pipestr
from scripts.render_cli import show_cli_output
import ipaddress


def bgp_global_path():
    """Returns the base path for BGP global configuration"""
    return Path("/restconf/data/openconfig-bgp:bgp/global")


def bgp_global_config_path():
    """Returns the path for BGP global config container"""
    return Path("/restconf/data/openconfig-bgp:bgp/global/config")


def prefix_sets_path():
    """Returns the base path for prefix sets"""
    return Path("/restconf/data/openconfig-routing-policy:routing-policy/defined-sets/prefix-sets")


def prefix_set_path(name):
    """Returns the path for a specific prefix set"""
    return Path("/restconf/data/openconfig-routing-policy:routing-policy/defined-sets/prefix-sets/prefix-set={name}", name=name)

def bgp_neighbor_path(neighbor_ip):
    """Returns the path for a specific BGP neighbor"""
    return Path("/restconf/data/openconfig-bgp:bgp/neighbors/neighbor={neighbor_address}",
                neighbor_address=neighbor_ip)


def check_ok(resp):
    """Check if response is OK and print error if not"""
    if not resp.ok():
        print(resp.error_message())
        return 1
    return 0


def render(path, template):
    """Get data from API and render using template"""
    resp = get_openconfig_bgp_bgp_global(path)
    if not resp.ok():
        print(resp.error_message())
        return 1
    if resp.content:
        show_cli_output(template, resp.content)
    return 0


def get_openconfig_bgp_bgp_global(path):
    return ApiClient().get(path, ignore404=True)


class Handlers:

    # ==========================================================================
    # router bgp handlers
    # ==========================================================================

    @staticmethod
    def show_openconfig_bgp_bgp_global_config(template, *args):
        """Get BGP global configuration"""
        return render(bgp_global_path(), template)

    @staticmethod
    def post_openconfig_bgp_bgp_global(as_number, router_id):
        """Create BGP global configuration using POST"""
        body = {
            "openconfig-bgp:config": {
                "as": int(as_number),
                "router-id": router_id
            }
        }
        resp = ApiClient().post(bgp_global_path(), body)
        if not resp.ok():
            if "configuration already exists" in resp.error_message():
                resp = get_openconfig_bgp_bgp_global(bgp_global_path())
                bgp_asn = resp.content['openconfig-bgp:global']['config']['as']
                if bgp_asn == int(as_number):
                    return 0
                print(f"BGP instance is already running; AS is {bgp_asn}")
                print(
                    f"Remove existing configuration ('no router bgp {bgp_asn}') before adding a new one.")
            else:
                print(resp.error_message())
            return 1
        return 0

    @staticmethod
    def patch_openconfig_bgp_bgp_global_config(as_number, router_id):
        """Update BGP global configuration using PATCH"""
        body = {
            "openconfig-bgp:config": {
                "as": int(as_number),
                "router-id": router_id
            }
        }
        resp = ApiClient().patch(bgp_global_config_path(), body)
        return check_ok(resp)

    @staticmethod
    def put_openconfig_bgp_bgp_global_config(as_number, router_id):
        """Replace BGP global configuration using PUT"""
        body = {
            "openconfig-bgp:config": {
                "as": int(as_number),
                "router-id": router_id
            }
        }
        resp = ApiClient().put(bgp_global_config_path(), body)
        return check_ok(resp)

    @staticmethod
    def delete_openconfig_bgp_bgp_global():
        """Delete BGP global configuration"""
        resp = ApiClient().delete(bgp_global_path())
        return check_ok(resp)

    # ==========================================================================
    # ip prefix-list handlers
    # ==========================================================================

    @staticmethod
    def get_openconfig_routing_policy_defined_sets_prefix_sets(template, *args):
        """Get all prefix sets"""
        return render(prefix_sets_path(), template)

    @staticmethod
    def put_openconfig_routing_policy_defined_sets_prefix_sets_prefix_set(name, action, ip_prefix, range_le=None, range_ge=None):
        """Update an existing prefix set using PUT"""
        try:
            addr = ipaddress.ip_network(ip_prefix, strict=False)
        except Exception as e:
            print(f"{e.message}")
            return 1

        mode = "IPV4" if addr.version == 4 else "IPV6"
        try:
            mask_le = ip_prefix.split('/')[1]
        except Exception:
            print("Mask length is required for prefix-list entry")
            return 1

        if range_le is None and range_ge is None:
            oc_masklength_range = "exact"
        else:
            if range_le is None:
                le = int(mask_le)
                ge = int(range_ge)
            if range_ge is None:
                le = int(mask_le)
                ge = int(range_le)
            if range_le is not None and range_ge is not None:
                le = int(range_le)
                ge = int(range_ge)
            max_bits = 32 if addr.version == 4 else 128
            if not (0 <= le <= max_bits):
                print(
                    f"Bad len params: {le}..{ge}. Min length must be between 0 and {max_bits} for {'IPv4' if addr.version == 4 else 'IPv6'}")
                return 1
            if not (0 <= ge <= max_bits):
                print(
                    f"Bad len params: {le}..{ge}. Max length must be between 0 and {max_bits} for {'IPv4' if addr.version == 4 else 'IPv6'}")
                return 1
            if le > ge:
                print(f"Bad len params: {le}..{ge}. Min length cannot be greater than max length")
                return 1
            oc_masklength_range = f"{le}..{ge}"

        if action == "permit":
            oc_action = "ACCEPT_ROUTE"
        else:
            oc_action = "REJECT_ROUTE"

        body = {
            "openconfig-routing-policy:prefix-set": [{
                "name": name,
                "config": {
                    "name": name,
                    "mode": mode
                },
                "prefixes": {
                    "prefix": [{
                        "ip-prefix": ip_prefix,
                        "masklength-range": oc_masklength_range,
                        "config": {
                            "ip-prefix": ip_prefix,
                            "masklength-range": oc_masklength_range,
                            "action": oc_action
                        }
                    }]
                }
            }]
        }
        resp = ApiClient().put(prefix_set_path(name), body)
        return check_ok(resp)

    @staticmethod
    def delete_openconfig_routing_policy_defined_sets_prefix_sets_prefix_set(name):
        """Delete a prefix set"""
        resp = ApiClient().delete(prefix_set_path(name))
        return check_ok(resp)

    # ==========================================================================
    # bgp-neighbor handlers
    # ==========================================================================
    @staticmethod
    def get_openconfig_bgp_bgp_neighbors_neighbor(neighbor_ip, template, *args):
        """Get BGP neighbor configuration"""
        path = bgp_neighbor_path(neighbor_ip)
        return render(path, template)

    @staticmethod
    def put_openconfig_bgp_bgp_neighbors_neighbor(neighbor_addr, remote_asn=None, name=None, local_addr=None):
        """Configure BGP neighbor attributes"""
        body = {
            "openconfig-bgp:neighbor": [{
                "neighbor-address": neighbor_addr,
                "config": {
                    "neighbor-address": neighbor_addr,
                },
            }]
        }
        if remote_asn is not None:  
            body["openconfig-bgp:neighbor"][0]["config"]["peer-as"] = int(remote_asn)
        if name is not None:
            body["openconfig-bgp:neighbor"][0]["config"]["description"] = name
        if local_addr is not None:  
            body["openconfig-bgp:neighbor"][0]["transport"] = {
                "config": {
                    "local-address": local_addr
                }
            }

        resp = ApiClient().put(bgp_neighbor_path(neighbor_addr), body)
        return check_ok(resp)

    @staticmethod
    def put_openconfig_bgp_bgp_neighbors_neighbor_remote_as(neighbor_ip, remote_as_number):
        """Configure BGP neighbor remote AS"""
        path = bgp_neighbor_path(neighbor_ip)
        body = {
            "openconfig-bgp:neighbor": [{
                "neighbor-address": neighbor_ip,
                "config": {
                    "neighbor-address": neighbor_ip,
                    "peer-as": int(remote_as_number)
                }
            }]
        }
        resp = ApiClient().put(path, body)
        return check_ok(resp)

    @staticmethod  
    def put_openconfig_bgp_bgp_neighbors_neighbor_description(neighbor_ip, name):
        """Configure BGP neighbor description"""
        path = bgp_neighbor_path(neighbor_ip)
        body = {
            "openconfig-bgp:neighbor": [{
                "neighbor-address": neighbor_ip,
                "config": {
                    "neighbor-address": neighbor_ip,
                    "description": name
                }
            }]
        }
        resp = ApiClient().put(path, body)
        return check_ok(resp)
  
    @staticmethod
    def put_openconfig_bgp_bgp_neighbors_neighbor_update_source(neighbor_ip, local_address):
        """Configure BGP neighbor update source"""
        path = bgp_neighbor_path(neighbor_ip)
        body = {
            "openconfig-bgp:neighbor": [{
                "neighbor-address": neighbor_ip,
                "transport": {
                    "config": {
                        "local-address": local_address
                    }
                }
            }]
        }
        resp = ApiClient().put(path, body)
        return check_ok(resp)

    @staticmethod
    def delete_openconfig_bgp_bgp_neighbors_neighbor(neighbor_ip):
        """Delete BGP neighbor configuration"""
        path = bgp_neighbor_path(neighbor_ip)
        resp = ApiClient().delete(path)
        return check_ok(resp)


def run(func, args):
    """Execute the specified handler function"""
    return getattr(Handlers, func)(*args)


if __name__ == '__main__':
    pipestr().write(sys.argv)
    func = sys.argv[1]
    run(func, sys.argv[2:])
