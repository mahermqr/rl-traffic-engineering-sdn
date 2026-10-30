#!/usr/bin/env python3
"""Launch Ryu 4.34 with the Eventlet compatibility shim it requires."""

import eventlet.wsgi


# Ryu 4.34 imports this legacy sentinel. Eventlet removed it after 0.30.
if not hasattr(eventlet.wsgi, "ALREADY_HANDLED"):
    eventlet.wsgi.ALREADY_HANDLED = object()

from ryu.cmd.manager import main  # noqa: E402


if __name__ == "__main__":
    main()
