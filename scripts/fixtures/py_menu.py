# 夹具：应当只被报出 tag_switch / handrolled_observer_machinery。
class MenuBuilder:
    def __init__(self):
        self.cbs = []
        self.obs = []

    def add_listener(self, cb):
        self.cbs.append(cb)

    def remove_listener(self, cb):
        self.cbs.remove(cb)

    def add_observer(self, ob):
        self.obs.append(ob)

    def choose(self, kind: str):
        match kind:
            case "cheese":
                return CheesePie()
            case "veggie":
                return VeggiePie()
            case "clam":
                return ClamPie()
        return None
