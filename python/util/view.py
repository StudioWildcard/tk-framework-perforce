from http import client
from P4 import P4Exception, Map as P4Map  # Prefix P4 for consistency

import sgtk
from sgtk import TankError


def get_client_view(p4):
    """
    Get the view/mapping for the current workspace and user (as set
    in the p4 instance)

    :param p4:    The Perforce connection to use
    :returns:     The workspace root directory if found
    """
    try:
        client_spec = p4.fetch_client(p4.client)
        # if hasattr(client_spec, "_view"):
        #     return client_spec._view
        return []
    except P4Exception as e:
        raise TankError(
            "Perforce: Failed to query the workspace view/mapping for user '%s', workspace '%s': %s"
            % (p4.user, p4.client, p4.errors[0] if p4.errors else e)
        )


def add_paths_to_view(p4, paths):
    # convert paths to make sure works with
    views = []
    if not type(paths) is list:
        paths = [paths]
    for path in paths:
        pair_str = f"//{path}   //{p4.client}/{path}"
        views.append(pair_str)
    return set_client_view(p4, views)


def set_client_view(p4, view: list):
    """
    Get the view/mapping for the current workspace and user (as set
    in the p4 instance)

    :param p4:    The Perforce connection to use
    :returns:     The workspace root directory if found
    """
    try:
        client_spec = p4.fetch_client(p4.client)
        # view = client_spec.get("View")
        # if not view:
        client_spec["View"] = view
        p4.save_client(client_spec)
        return p4
    except P4Exception as e:
        raise TankError(
            "Perforce: Failed to query the workspace view/mapping for user '%s', workspace '%s': %s"
            % (p4.user, p4.client, p4.errors[0] if p4.errors else e)
        )
