import configparser

class astralStorage(object):
    def __init__(self):
        print("[storage] loading astral.ini")
        self.globalConfig = configparser.ConfigParser(allow_no_value=True)
        self.globalConfig.read("astral.ini")

    def getGlobalOption(self, opt):
        print(f"[storage] returning {opt}")
        return self.globalConfig.get("astral", opt).strip()
	
    def setGlobalOption(self, opt, val):
        print(f"[storage] setting {val} for {opt}")
        self.globalConfig.set("astral", opt, val)

astralStorage = astralStorage()