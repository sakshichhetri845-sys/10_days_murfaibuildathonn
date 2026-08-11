"""
Alias for CLI outbound dialing.
Forwards to src.telephony.outbound.dial.
"""

import sys

try:
    from src.telephony.outbound.dial import main
except ImportError:
    from telephony.outbound.dial import main

if __name__ == "__main__":
    sys.exit(main())
