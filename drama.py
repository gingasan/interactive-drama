import math
from dataclasses import dataclass
from utils import *


class Drama:
    def __init__(self, id, script):
        self.id = id
        self.script = DynamicScript(script)

        self.player = None
        self.characters = {}

        self.timestamp = 0
        self.cache = {}
        self.records = []

        self.characters_jogai = {}

        self.memory_to_text = memory_to_text
        self.ready_for_next_scene = False

        self.reset()

    @property
    def state(self):
        state = {
            "player": self.player.state,
            "characters": {char_id: char.state for char_id, char in self.characters.items() if char_id != self.player.id},
            "records": self.records,
            "scene": "{}——{}".format(self.script.scene_id, self.script["名称"])
        }
        return state

    def reset(self):
        self.player = None
        self.characters.clear()
        self.timestamp = 0
        self.records.clear()
        self.script.p = 0

    def add_character(self, char, loc, as_player=False):
        self.characters[char.id] = char
        char._loc = loc
        char.loc = self.script.location
        if as_player:
            self.player = self.characters[char.id]
        for _, char in self.characters.items():
            self.update_view(char.id)

    def update_view(self, character_id):
        src = self.characters[character_id]
        view = {"items": {}, "characters": {}}
        for _, char in self.characters.items():
            if char.id == character_id:
                continue
            view["characters"].update({char.id: char.surface})
        src.update_view(view)

    def calculate(self, aid, x, bid=None, cid=None, **kwargs):
        print(self.script.mode, " - ", aid, x, bid, kwargs.get("content"))
        if x == "-stay":
            return
        if self.script.mode == "v1" or self.script.mode == "v2":
            assert x == "-speak"
            src = self.characters[aid]
            for t in self.characters:
                self.characters[t].new_memory(src.id, "-speak", None, content=kwargs["content"])
            self.record(aid, x, None, cid, **kwargs)
        elif self.script.mode == "ex":
            self._calculate(aid, x, bid, cid, **kwargs)

    def _calculate(self, aid, x, bid=None, cid=None, **kwargs):
        src = self.characters[aid]
        if x == "-move":
            if bid in self.characters:
                ax = self.characters[bid]._loc[0]
                ay = self.characters[bid]._loc[1]
                ax += rndc([-20, -10, 10, 20])
                ay += rndc([-20, -10, 10, 20])
            elif bid in self.scenes:
                ax = self.scenes[bid].center[0]
                ay = self.scenes[bid].center[1]
                ax += rndc([-5, 0, 5])
                ay += rndc([-5, 0, 5])
            src._loc = (ax, ay)
            src.new_memory(src.id, "-move", bid)
            src.to_do = True
            if src.interact_with:
                trg = src.interact_with
                trg.new_memory(src.id, "-leave", src.interact_with.id)
                trg.interact_with = None
                trg.to_do = None
                src.interact_with = None
                trg.recent_memory.clear()
                src.recent_memory.clear()
        elif x == "-leave":
            trg = src.interact_with
            trg.new_memory(src.id, "-leave", src.interact_with.id)
            src.new_memory(src.id, "-leave", src.interact_with.id)
            trg.interact_with = None
            trg.to_do = None
            src.interact_with = None
            src.to_do = None
            trg.recent_memory.clear()
            src.recent_memory.clear()
        if x in ["-move", "-stay", "-leave"]:
            return

        if src.interact_with is not None:
            if bid is None or bid == src.interact_with.id:
                src.interact(x, cid, **kwargs)
            else:
                trg = src.interact_with
                trg.new_memory(src.id, "-leave", src.interact_with.id)
                src.new_memory(src.id, "-leave", src.interact_with.id)
                trg.interact_with = None
                trg.to_do = None
                src.interact_with = self.characters[bid]
                self.characters[bid].interact_with = src
                src.interact(x, cid, **kwargs)
        else:
            src.interact_with = self.characters[bid]
            self.characters[bid].interact_with = src
            src.interact(x, cid, **kwargs)

        self.record(aid, x, bid, cid, **kwargs)

    def record(self, aid, x, bid, cid, **kwargs):
        m = {"aid": aid, "x": x, "bid": bid, "cid": cid, **kwargs}
        self.records.append(self.memory_to_text(m))

    def __repr__(self):
        return "{}".format(self.state)
    
    def freeze(self, character_id):
        target = self.characters.pop(character_id)
        self.characters_jogai.update({character_id: target})

    def unfreeze(self, character_id):
        target = self.characters_jogai.pop(character_id)
        self.characters.update({character_id: target})

    def next_scene(self):
        self.script.p += 1
        for char_id in self.characters:
            self.characters[char_id].interact_with = None
            self.characters[char_id].to_do = False
        self.ready_for_next_scene = False

        for k, v in self.script.characters.items():
            if k not in self.characters:
                self.unfreeze(k)
            self.characters[k].motivation = v


class Character:
    def __init__(self, id=None, config={}):
        self.id = id if id else config.get("id")
        self.id_2 = config.get("id_2")
        self.profile = config.get("profile", "")

        # Status, init idle
        self.status = "/idle/"
        # Location
        self._loc = (-1, -1)
        self.loc = None
        # Memory
        self.memory = []
        # View
        self.view = []

        # Holdings (items)
        self.holdings = {}

        self.interact_with = None
        self.to_do = None
        self.recent_memory = []

        self.memory_to_text = memory_to_text
        self.observation_to_text = observation_to_text

    @property
    def ops(self):
        return ["-speak", "-give", "-stay", "-leave"]

    @property
    def surface(self):
        return {
            "id": self.id,
            "status": self.status,
            "interact_with": self.interact_with.id if self.interact_with else None,
            "loc": self.loc
        }

    @property
    def state(self):
        state = {
            "id": self.id,
            "id_2": self.id_2,
            "status": self.status,
            "interact_with": self.interact_with.id if self.interact_with else None,
            "loc": self._loc,
            "holdings": [v.state for k, v in self.holdings.items()],
            "memory": self.memory,
            "view": self.view
        }
        return state

    def interact(self, x, cid=None, **kwargs):
        if x == "-speak":
            self.speak(kwargs["content"])
        elif x == "-give":
            self.give(cid)

    def speak(self, content):
        trg = self.interact_with
        trg.new_memory(self.id, "-speak", trg.id, content=content)
        self.new_memory(self.id, "-speak", trg.id, content=content)
        trg.to_do = True
        self.to_do = False

    def give(self, cid):
        assert cid in self.holdings
        trg = self.interact_with
        trg.into_hold(self.outof_hold(self.holdings[cid]))
        trg.new_memory(self.id, "-give", trg.id, cid=cid)
        self.new_memory(self.id, "-give", trg.id, cid=cid)
        trg.to_do = True
        self.to_do = False

    def update_view(self, new_view):
        self.view.clear()
        for v in new_view["characters"].values():
            self.view.append(self.observation_to_text(v, self.id))

    def new_memory(self, aid=None, x=None, bid=None, cid=None, **kwargs):
        if self.status == "/faint/":
            return

        if kwargs.get("text"):
            self.memory.append(kwargs["text"])
            return

        m = {"aid": aid, "x": x, "bid": bid, "cid": cid, **kwargs}
        self.memory.append(self.memory_to_text(m, self.id))
        self.recent_memory.append(self.memory_to_text(m, self.id))

    def into_hold(self, item):
        item.owner = self.id
        self.holdings[item.id] = item

    def outof_hold(self, item):
        if isinstance(item, str):
            item = self.holdings[item]
        item.owner = None
        return self.holdings.pop(item.id)
    
    def __repr__(self):
        return "{}".format(self.state)


class CharacterLLM(Character):
    def __init__(self, id=None, config={}, query_fct=query_gpt4):
        super().__init__(id, config)
        self.motivation = None
        self.narrative = None
        self.plan = None
        self.decision = []

        self.query_fct = query_fct

        self.prompt = read("prompt/prompt_character_v2.md")
        self.cache_dir = "cache/"

    def log(self, content, suffix):
        with open(os.path.join(self.cache_dir, self.id, suffix), "w") as f:
            f.write(content)

    def act(self):
        while not self.decision:
            self.make_plan()        
        next_act = self.decision.pop(0)

        return next_act

    def make_plan(self):
        prompt = self.prompt.format(id=self.id,
                                    profile=self.profile,
                                    memory=dumps(self.memory),
                                    view=dumps(self.view),
                                    interact_with=self.interact_with.id if self.interact_with else "",
                                    recent_memory=dumps(self.recent_memory),
                                    holdings=dumps([v.state for k, v in self.holdings.items()]),
                                    motivation=self.motivation,
                                    narrative=yamld(self.narrative))

        response = self.query_fct([{"role": "user", "content": prompt}])
        self.log("\n".join([prompt, response]), "plan")

        response = json.loads(response.split("```json\n")[-1].split("\n```")[0])
        plan = response.get("当前的计划", self.plan)
        decision = response["决策"]

        self.plan = plan
        self.decision += [decision]


@dataclass
class Item:
    id: str
    description: str
    owner: str = None

    @property
    def state(self):
        return {
            "id": self.id,
            "description": self.description,
            "owner": self.owner
        }


class DramaLLM(Drama):
    def __init__(self, id, script, query_fct=query_gpt4):
        super().__init__(id, script)
        self.nc = {}
        self.instructs = {}
        self.reset()

        self.query_fct = query_fct

        self.prompt_v1 = read("prompt/prompt_drama_v1.md")
        self.cache_dir = "cache/"

    def v1(self):
        prompt = self.prompt_v1.format(
            npcs="\n\n".join(["\n".join([char_id, char.profile.strip()]) for char_id, char in self.characters.items() if char_id != self.player.id]),
            player_id=self.player.id,
            script=self.script.dump(),
            scene_id=self.script.scene_id,
            narrative=dumps(self.nc),
            records="\n".join([line for line in self.records]),
            recent=dumps(self.records[-3:])
        )

        response = self.query_fct([{"role": "user", "content": prompt}])
        self.log("\n".join([prompt, response]), "v1")

        response = json.loads(response.split("```json\n")[-1].split("\n```")[0])

        self.nc = response["当前的情节链"]
        decision = response["决策"]
        self.characters.get(decision["aid"]).decision.append(decision)
        for char_id in self.characters:
            self.characters[char_id].to_do = True if char_id == decision["aid"] else False

        if all([t == True for _, t in self.nc]):
            self.ready_for_next_scene = True

    def log(self, content, suffix):
        with open(os.path.join(self.cache_dir, "drama", suffix), "w") as f:
            f.write(content)
