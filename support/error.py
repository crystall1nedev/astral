from enum import Enum

class _astral_error_mixin(Enum):
    """
    Small class used internally to provide extra properties for the error Enum.

    Don't use this.
    """
    def __new__(cls, critical, message): 
        obj = object.__new__(cls) 
        obj._value_ = message 
        obj.critical = critical 
        return obj

class astral_error:
    """
    Enum with sub-enums that define common errors used throughout astral's codebase.

    Organized as such:
    - Global, critical errors
    - Server, critical errors
    - Global, non-critical errors
    - Server, non-critical errors

    Critical errors should always be dealt with properly. Since these aren't Exceptions, you don't
    always need to catch them as such - just cancelling the current task is fine in those cases.
    Non-critical errors can safely be continued on, as long as you provide defaults in code.
    """
    class bot(_astral_error_mixin):
        """
        Common errors tied to bot initialization or other general bot-wide faults.
        """
        undef_token            = (True,  "Token not defined")

    class escpos(_astral_error_mixin):
        """
        Common errors tied to the ESC/POS cog.
        """
        undef_ip               = (True,  "ESC/POS IP address not defined")
        undef_profile          = (True,  "ESC/POS profile not defined")

        undef_server           = (True,  "ESC/POS current server not configured")

        undef_port             = (False, "ESC/POS port not defined")
        undef_verbosity        = (False, "ESC/POS verbosity enablement not defined")
        undef_multitone        = (False, "ESC/POS multitone enablement not defined")

class astral_exception(Exception):
    def __init__(self, error_enum): 
        super().__init__(error_enum.value) 
        self.error = error_enum

