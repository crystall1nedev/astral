import configparser, os
from asyncio import sleep 
from discord import Member
class astralStorage(object):
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
    def saveConfigsToDisk(self):
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
    def getServerInt(self, server, section, opt) -> int:
        val = self.getServerOption(server, section, opt)
        return int(val) if val is not None else None
    def getServerFloat(self, server, section, opt) -> float:   
        val = self.getServerOption(server, section, opt)
        return float(val) if val is not None else None
    def getServerStr(self, server, section, opt) -> str:  
        val = self.getServerOption(server, section, opt)
        return val if val is not None else None
    def getServerBool(self, server, section, opt) -> bool:     
        val = self.getServerOption(server, section, opt)
        return bool(val) if val is not None else None
    def getServerStrList(self, server, section, opt) -> list:  
        val = self.getServerOption(server, section, opt)
        return list(map(str.strip, val.split(","))) if val is not None else None
    def getServerIntList(self, server, section, opt) -> list:  
        val = self.getServerOption(server, section, opt)
        return list(map(int, val.split(","))) if val is not None else None
    # Gets a raw string value from server specific .ini
    def getServerOption(self, server, section, opt):
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
    def setServerInt(self, server, section, opt, val):   self.setServerOption(server, section, opt, (str(val)))
    def setServerFloat(self, server, section, opt, val): self.setServerOption(server, section, opt, (str(val)))
    def setServerStr(self, server, section, opt, val):   self.setServerOption(server, section, opt, (str(val)))
    def setServerBool(self, server, section, opt, val):  self.setServerOption(server, section, opt, "true" if val else "false")
    def setServerList(self, server, section, opt, val):  self.setServerOption(server, section, opt, (str(",".join(map(str, val)))))
    # Sets a raw string value in server specific .ini
    def setServerOption(self, server, section, opt, val):
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
    def getGlobalInt(self, section, opt) -> int:     
        val = self.getGlobalOption(section, opt)
        return int(val) if val is not None else None
    def getGlobalFloat(self, section, opt) -> float: 
        val = self.getGlobalOption(section, opt)
        return float(val) if val is not None else None
    def getGlobalStr(self, section, opt) -> str:     
        val = self.getGlobalOption(section, opt)
        return val if val is not None else None
    def getGlobalBool(self, section, opt) -> bool:   
        val = self.getGlobalOption(section, opt)
        return bool(val) if val is not None else None
    def getGlobalStrList(self, section, opt) -> list:  
        val = self.getGlobalOption(section, opt)
        return list(map(str.strip, val.split(","))) if val is not None else None
    def getGlobalIntList(self, section, opt) -> list:   
        val = self.getGlobalOption(section, opt)
        return list(map(int, val.split(","))) if val is not None else None
    # Gets a raw string value from astral.ini
    def getGlobalOption(self, section, opt):
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
    def setGlobalInt(self, section, opt, val):   self.setGlobalOption(section, opt, (str(val)))
    def setGlobalFloat(self, section, opt, val): self.setGlobalOption(section, opt, (str(val)))
    def setGlobalStr(self, section, opt, val):   self.setGlobalOption(section, opt, (str(val)))
    def setGlobalBool(self, section, opt, val):  self.setGlobalOption(section, opt, "true" if val else "false")
    def setGlobalList(self, section, opt, val):  self.setGlobalOption(section, opt, (str(",".join(map(str, val)))))
    # Sets a raw string value in astral.ini
    def setGlobalOption(self, section, opt, val):
        print(f"[storage] setting {val} for global section {section} option {opt}")
        self.globalConfig.set(section, opt, val)
    
    # Checks whether or not the passed int is in the owners list.
    def isCallerOwner(self, user: Member) -> bool:
        # Disable the ability to run all owner-only commands by default.
        # This is overriden manually by config.py's addOwner.
        return self.isCallerEntitledFor(user, False, astralStorage.getGlobalIntList("astral", "owners"))
    
    def isCallerEntitledFor(self, user: Member, shouldCheckRoles: bool, array: list = None) -> bool:
        if array is None:   return False
        if len(array) == 0: return False
        if shouldCheckRoles:
            return any(role_id in [role.id for role in user.roles] for role_id in array)
        else:
            return user.id in array



    

astralStorage = astralStorage()