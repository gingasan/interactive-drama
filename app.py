from drama import *
from flask import Flask, jsonify, request
from flask_cors import CORS
import time


class ADramaLLM(DramaLLM):
    def reset(self):
        super().reset()

        KeN = Character("柯南", {"id_2": "kn", "profile": SCRIPT["character"]["柯南"]})
        XiaoWL = CharacterLLM("毛利小五郎", {"id_2": "mlxwl", "profile": SCRIPT["character"]["毛利小五郎"]})
        Lan = CharacterLLM("毛利兰", {"id_2": "mll", "profile": SCRIPT["character"]["毛利兰"]})
        XiongY = CharacterLLM("雄一", {"id_2": "syxy", "profile": SCRIPT["character"]["雄一"]})
        MoLS = CharacterLLM("莫里斯", {"id_2": "mls", "profile": SCRIPT["character"]["莫里斯"]})
        Jun = CharacterLLM("均", {"id_2": "wsj", "profile": SCRIPT["character"]["均"]})
        JiZ = CharacterLLM("纪子", {"id_2": "lqjz", "profile": SCRIPT["character"]["纪子"]})
        YaZ = CharacterLLM("雅子站员", {"id_2": "syyz", "profile": SCRIPT["character"]["雅子站员"]})
        JiuX = CharacterLLM("久雄站长", {"id_2": "zz", "profile": SCRIPT["character"]["久雄站长"]})
        self.add_character(KeN, (307, 472), as_player=True)
        self.add_character(XiaoWL, (250, 420))
        self.add_character(Lan, (300, 420))
        self.add_character(XiongY, (110, 500))
        self.add_character(MoLS, (200, 500))
        self.add_character(Jun, (160, 510))
        self.add_character(JiZ, (110, 350))
        self.add_character(YaZ, (200, 280))
        self.add_character(JiuX, (260, 290))

        self.nc = [[plot, False] for plot in self.script.plots]
        self.calculate(aid="毛利小五郎", x="-speak", content="说起来真是太惊人了，没想到回东京这天会突然刮起台风。")

    def next_scene(self):
        super().next_scene()

        self.nc = [[plot, False] for plot in self.script.plots] if self.script.plots else None

        if self.script.scene_id == "场景2":
            self.characters["柯南"]._loc = (590, 350)
            self.characters["毛利小五郎"]._loc = (600, 390)
            self.characters["雄一"]._loc = (670, 390)
            self.characters["莫里斯"]._loc = (660, 350)
            self.freeze("均")
            self.freeze("纪子")
            self.freeze("雅子站员")
            self.freeze("久雄站长")
            self.freeze("毛利兰")
    
        elif self.script.scene_id == "场景3":
            self.characters["柯南"]._loc = (290, 370)
            self.characters["柯南"].into_hold(Item(id="神秘的字条", description="一张神秘的字条，字迹潦草——毛利先生，今晚将有人在这里被杀，凶手是——看上去写字条的人很匆忙，没来得及写完。"))
            self.characters["雄一"]._loc = (360, 510)
            self.characters["莫里斯"]._loc = (260, 510)
            self.characters["均"]._loc = (160, 400)
            self.characters["纪子"]._loc = (110, 350)
            self.characters["雅子站员"]._loc = (200, 280)
            self.characters["久雄站长"]._loc = (350, 330)
            self.characters["毛利兰"]._loc = (110, 490)
            self.freeze("毛利小五郎")
            # self.ready_for_next_scene = True


with open("script_zh.yaml") as file:
    SCRIPT = yaml.safe_load(file)
DRAMA = ADramaLLM("alpha", SCRIPT["narrative"])
app = Flask(__name__)
CORS(app)
PPROX = read("proxy.txt")


def get_input(data):
    aid = data.get("aid")
    x = data.get("x")
    bid = data.get("bid")
    cid = data.get("cid")
    content = data.get("content")
    _loc = (data.get("loc_x"), data.get("loc_y"))

    return aid, x, bid, cid, content, _loc


@app.route("/init")
def init():
    DRAMA.reset()
    return jsonify(DRAMA.state)


@app.route("/calculate", methods=["POST"])
def calculate():        
    data = request.get_json()

    aid, x, bid, cid, content, _loc = get_input(data)
    assert aid == DRAMA.player.id
    DRAMA.player._loc = _loc

    reflect = False
    if (DRAMA.timestamp + 1) % 5 == 0:
        reflect = True

    t1 = time.time()
    if DRAMA.script.mode == "v1":
        DRAMA.calculate(aid=aid, x=x, bid=bid, cid=cid, content=content)
        if reflect:
            DRAMA.reflect()
        DRAMA.v1()
    elif DRAMA.script.mode == "ex":
        DRAMA.calculate(aid=aid, x=x, bid=bid, cid=cid, content=content)
        if reflect:
            DRAMA.reflect()

    state = {"move": {}, "dialogues": {}}
    for char_id, char in DRAMA.characters.items():
        DRAMA.update_view(char_id)
        if char_id == DRAMA.player.id:
            continue

        if char.status == "/faint/":
            continue

        if not char.to_do:
            continue

        decision = char.act()
        _, x, b, c, content, _ = get_input(decision)

        if x == "-speak":
            state["dialogues"][char_id] = content
            DRAMA.calculate(char_id, x, b, None, content=content)
        elif x == "-move":
            state["move"][char_id] = {"start": DRAMA.characters[char_id]._loc}
            DRAMA.calculate(char_id, x, b, None)
        else:
            DRAMA.calculate(char_id, x, b, c)
    
    t2 = time.time()
    print("Take {}s".format(round(t2 - t1, 2)))

    for char_id in state["move"]:
        state["move"][char_id].update({"end": DRAMA.characters[char_id]._loc})

    state.update(DRAMA.state)

    return jsonify(state)


@app.route("/next_scene")
def next_scene():
    state = {"move": {}, "dialogues": {}}
    loc = DRAMA.player._loc
    
    DRAMA.next_scene() # For debug
    # if DRAMA.ready_for_next_scene:
    #     DRAMA.next_scene()

    new_loc = DRAMA.player._loc
    if new_loc != loc:
        state["move"] = {DRAMA.player.id: {"start": loc, "end": new_loc}}

    state.update(DRAMA.state)
    return jsonify(state)


@app.route("/get_ops", methods=["POST"])
def get_ops():
    bid = request.get_json()
    if DRAMA.player.interact_with is None:
        ops = DRAMA.player.ops
        ops.remove("-leave")
    elif bid == DRAMA.player.interact_with.id:
        ops = DRAMA.player.ops
    else:
        return []
    return jsonify(ops)


@app.route("/export_records")
def export_records():
    write_json(DRAMA.records, "records/%s-%s" % (date(), rndsuf()))
    return jsonify(DRAMA.records)


if __name__ == "__main__":
    app.run(debug=True)
