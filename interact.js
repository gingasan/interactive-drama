function start_interact(scene, target) {
    const distance = Phaser.Math.Distance.Between(player.x, player.y, target.x, target.y);
    if (distance > 80) return;

    fetch("http://127.0.0.1:5000/get_ops", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(target.id)
    })
    .then(response => response.json())
    .then(data => {
        const options = data;

        const dropdown = document.getElementById("user-acts");
        dropdown.options.length = 0;

        options.forEach(option => {
            const newOption = document.createElement("option");
            newOption.value = option;
            newOption.textContent = option;
            dropdown.add(newOption);
        });

        const display = document.getElementById("user-target");
        display.value = target.id;
        display.textContent = target.id;

        const codeDisplay = document.querySelector(".code-display");
        if (!codeDisplay.classList.contains("open")) {
            codeDisplay.classList.add("open");
        }
    });
}

function do_interact(scene) {
    isBusy = true;
    const button = document.getElementById("user-confirm");
    button.disabled = true;

    const act = document.getElementById("user-acts").value;
    const bid = document.getElementById("user-target").value;
    const cid = document.getElementById("user-item").value;
    const content = document.getElementById("user-content").value;

    const input_data = {
        aid: player.id,
        x: act,
        bid: bid,
        cid: cid,
        content: content,
        loc_x: player.x,
        loc_y: player.y
    };
    console.log(input_data)

    if (act == "对话") {
        showDialogue(scene, player, content);
    }

    fetch("http://127.0.0.1:5000/calculate", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(input_data)
    })
    .then(response => response.json())
    .then(data => {
        state = data;

    });

    isBusy = false;
    button.disabled = false;
}

function stay(scene) {
    isBusy = true;

    const input_data = {
        aid: player.id,
        x: "等待",
        loc_x: player.x,
        loc_y: player.y
    };

    fetch("http://127.0.0.1:5000/calculate", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(input_data)
    })
    .then(response => response.json())
    .then(data => {
        state = data;

    });

    isBusy = false;
}
