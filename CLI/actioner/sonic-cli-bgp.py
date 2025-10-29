import sys
from cli_client import ApiClient, Path
from rpipe_utils import pipestr
from scripts.render_cli import show_cli_output


def bgp_global_path():
    """Returns the base path for BGP global configuration"""
    return Path("/restconf/data/openconfig-bgp:bgp/global")


def bgp_global_config_path():
    """Returns the path for BGP global config container"""
    return Path("/restconf/data/openconfig-bgp:bgp/global/config")


def check_ok(resp):
    """Check if response is OK and print error if not"""
    if not resp.ok():
        print(resp.error_message())
        return 1
    return 0


def render(path, template):
    """Get data from API and render using template"""
    resp = ApiClient().get(path, ignore404=True)
    if not resp.ok():
        print(resp.error_message())
        return 1
    if resp.content:
        show_cli_output(template, resp.content)
    return 0


class Handlers:
    @staticmethod
    def get_openconfig_bgp_bgp_global(template, *args):
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
        return check_ok(resp)

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


def run(func, args):
    """Execute the specified handler function"""
    return getattr(Handlers, func)(*args)


if __name__ == '__main__':
    pipestr().write(sys.argv)
    func = sys.argv[1]
    run(func, sys.argv[2:])
