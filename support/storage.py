import configparser, os
import inspect
from asyncio import sleep 
from discord import Member, ApplicationContext
from support.error import astral_error, astral_exception
class astral_storage(object):
    # Object intended to hold individual server configurations
    # Don't access this directly; use the helpers.
    serverConfigs = {}

    # Initializer
    def __init__(self):
        # Being a little lenient here since we can assume defaults elsewhere
        print("[storage] loading astral.ini")
        self.globalConfig = configparser.ConfigParser(allow_no_value=True)

        # ...although if the file fails to load, we have a bigger issue.
        # Python will report the problem on its own though.
        if open("astral.ini", "r"):
            self.globalConfig.read("astral.ini")

        # Iterate through the files in the storage directory that end in
        # .ini, and load them into the serverConfigs dictionary.
        for filename in os.listdir("storage"):
            if filename.endswith(".ini"):
                if "example" in filename:
                    continue
                
                server_id = int(filename[:-4])

                print(f"[storage] loading {filename}")
                parser = configparser.ConfigParser()
                parser.read(os.path.join("storage", filename))

                self.serverConfigs[server_id] = parser
                print(self.serverConfigs)
    
    # Save configurations to disk, used by the autosave loop 
    # but can be called manually when necessary.
    def save_configs_to_disk(self):
        try:
            with open("astral.ini", "w") as configfile:
                print("[storage] saving astral.ini")
                self.globalConfig.write(configfile)
            for server in self.serverConfigs:
                filename = f"storage/{server}.ini"
                with open(filename, "w") as serverfile:
                    print(f"[storage] saving {serverfile.name}")
                    self.serverConfigs[server].write(serverfile)
        # This time Python won't do the Except-ing for us. Whatever is 
        # calling this function should catch this!
        except Exception as e:
            raise Exception(f"[storage] Saving failed: {e}\n[storage] All data is EPHEMERAL until this issue is fixed!!!")

    # Getter wrappers for easy outputs
    def get_server_int(self, server, section, opt) -> int:
        val = self.get_server_option(server, section, opt)
        return int(val) if val is not None else None
    def get_server_float(self, server, section, opt) -> float:   
        val = self.get_server_option(server, section, opt)
        return float(val) if val is not None else None
    def get_server_str(self, server, section, opt) -> str:  
        val = self.get_server_option(server, section, opt)
        return val if val is not None else None
    def get_server_bool(self, server, section, opt) -> bool:     
        val = self.get_server_option(server, section, opt)
        return bool(val) if val is not None else None
    def get_server_str_list(self, server, section, opt) -> list:  
        val = self.get_server_option(server, section, opt)
        return list(map(str.strip, val.split(","))) if val is not None else None
    def get_server_int_list(self, server, section, opt) -> list:  
        val = self.get_server_option(server, section, opt)
        return list(map(int, val.split(","))) if val is not None else None
    # Gets a raw string value from server specific .ini
    def get_server_option(self, server, section, opt):
        print(f"[storage] returning server {server} section {section} option {opt}")
        if server not in self.serverConfigs.keys():
            print("[storage] very bad state:")
            print(f"[storage] {server} not in serverconfigs")
            print(self.serverConfigs)
        
        cfg = self.serverConfigs.get(server)

        if cfg is None:
            print(f"[storage] wasn't able to find an existing configuration for {server}, making a new one")
            cfg = configparser.ConfigParser(allow_no_value=True)
            self.serverConfigs[server] = cfg

        if not cfg.has_section(section):
            print(f"[storage] wasn't able to find {section} in {server} config, making a new one")
            cfg.add_section(section)
            return None


        # Safe: fallback applies to missing option
        val = cfg.get(section, opt, fallback=None)
        return val.strip() if val else None
	
    # Setter wrappers for easy inputs
    def set_server_int(self, server, section, opt, val):   self.set_server_option(server, section, opt, (str(val)))
    def set_server_float(self, server, section, opt, val): self.set_server_option(server, section, opt, (str(val)))
    def set_server_str(self, server, section, opt, val):   self.set_server_option(server, section, opt, (str(val)))
    def set_server_bool(self, server, section, opt, val):  self.set_server_option(server, section, opt, "true" if val else "false")
    def set_server_list(self, server, section, opt, val):  self.set_server_option(server, section, opt, (str(",".join(map(str, val)))))
    # Sets a raw string value in server specific .ini
    def set_server_option(self, server, section, opt, val):
        print(f"[storage] setting server {server} section {section} option {opt} = {val}")

        # If it's not here, we need to make it
        cfg = self.serverConfigs.get(server)
        if cfg is None:
            print(f"[storage] server {server} is new, creating blank config")
            cfg = configparser.ConfigParser(allow_no_value=True)
            self.serverConfigs[server] = cfg

        # Same as above
        if not cfg.has_section(section):
            print(f"[storage] section [{section}] missing, creating it")
            cfg.add_section(section)

        cfg.set(section, opt, val)

    # Getter wrappers for easy outputs
    def get_global_int(self, section, opt) -> int:     
        val = self.get_global_option(section, opt)
        return int(val) if val is not None else None
    def get_global_float(self, section, opt) -> float: 
        val = self.get_global_option(section, opt)
        return float(val) if val is not None else None
    def get_global_str(self, section, opt) -> str:     
        val = self.get_global_option(section, opt)
        return val if val is not None else None
    def get_global_bool(self, section, opt) -> bool:   
        val = self.get_global_option(section, opt)
        return bool(val) if val is not None else None
    def get_global_str_list(self, section, opt) -> list:  
        val = self.get_global_option(section, opt)
        return list(map(str.strip, val.split(","))) if val is not None else None
    def get_global_int_list(self, section, opt) -> list:   
        val = self.get_global_option(section, opt)
        return list(map(int, val.split(","))) if val is not None else None
    # Gets a raw string value from astral.ini
    def get_global_option(self, section, opt):
        print(f"[storage] returning global section {section} option {opt}")
        cfg = self.globalConfig

        if cfg is None:
            raise Exception("[storage] Can't access global config, this is fatal!!!")

        if not cfg.has_section(section):
            cfg.add_section(section)
            return None

        val = cfg.get(section, opt, fallback=None)
        return val.strip() if val else None
	
    # Setter wrappers for easy inputs
    def set_global_int(self, section, opt, val):   self.set_global_option(section, opt, (str(val)))
    def set_global_float(self, section, opt, val): self.set_global_option(section, opt, (str(val)))
    def set_global_str(self, section, opt, val):   self.set_global_option(section, opt, (str(val)))
    def set_global_bool(self, section, opt, val):  self.set_global_option(section, opt, "true" if val else "false")
    def set_global_list(self, section, opt, val):  self.set_global_option(section, opt, (str(",".join(map(str, val)))))
    # Sets a raw string value in astral.ini
    def set_global_option(self, section, opt, val):
        print(f"[storage] setting {val} for global section {section} option {opt}")
        self.globalConfig.set(section, opt, val)
    
    # Checks whether or not the passed int is in the owners list.
    def is_caller_owner(self, user: Member) -> bool:
        # Disable the ability to run all owner-only commands by default.
        # This is overriden manually by config.py's addOwner.
        return self.is_caller_entitled_for(user, False, astral_storage.get_global_int_list("astral", "owners"))
    
    def is_caller_entitled_for(self, user: Member, shouldCheckRoles: bool, array: list = None) -> bool:
        if array is None:   return False
        if len(array) == 0: return False
        if shouldCheckRoles:
            return any(role_id in [role.id for role in user.roles] for role_id in array)
        else:
            return user.id in array

    def issue_with_configuration_present(self, env, error_array: list, ctx: ApplicationContext = None) -> astral_error:
        errors = []
        for err, var, getter, default in error_array:
            match len(inspect.signature(getter).parameters):
                case 0: value = getter()
                case 1: value = getter(ctx)
            setattr(env, var, value)
            if value is None: 
                if err.critical: 
                    errors.append(err)
                
                print(f"[storage] [verify] {err.value}")
                if default is not None:
                    print(f"[storage] [verify] Falling back to default value")
                    setattr(env, var, default)
        
        return errors if len(errors) > 0 else None

astral_storage = astral_storage()