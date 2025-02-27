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

    if (act == "-speak") {
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

    button.disabled = false;
}

function stay(scene) {
    const input_data = {
        aid: player.id,
        x: "-stay",
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

}

// function auto_interact(scene) {
//     const button = document.getElementById("user-confirm");
//     button.disabled = true;

//     const input_data = {
//         aid: player.id,
//         loc_x: player.x,
//         loc_y: player.y
//     };

//     fetch("http://127.0.0.1:5000/auto")
//         .then(response => response.json())
//         .then(data => {
//             Object.assign(input_data, data);

//             if (input_data.x == "-speak") {
//                 showDialogue(scene, player, input_data.content);
//             }
            
//             return fetch("http://127.0.0.1:5000/calculate", {
//                 method: "POST",
//                 headers: {
//                     "Content-Type": "application/json"
//                 },
//                 body: JSON.stringify(input_data)
//             });
//     })
//     .then(response => response.json())
//     .then(data => {
//         state = data;

//     });

//     button.disabled = false;
// }
async function auto_interact(scene) {
    const button = document.getElementById("user-confirm");
    button.disabled = true;

    const n = parseInt(document.getElementById("n-proxy").value);
    for (let i = 0; i < n; i++) {
        console.log(i + 1);
        const input_data = {
            aid: player.id,
            loc_x: player.x,
            loc_y: player.y
        };

        const autoResponse = await fetch("http://127.0.0.1:5000/auto");
        const autoData = await autoResponse.json();
        Object.assign(input_data, autoData);

        // Show dialogue if needed
        if (input_data.x == "-speak") {
            showDialogue(scene, player, input_data.content);
        }

        const calculateResponse = await fetch("http://127.0.0.1:5000/calculate", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(input_data)
        });

        const calculateData = await calculateResponse.json();
        state = calculateData;

    }

    button.disabled = false;
}