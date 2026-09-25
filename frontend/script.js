const questionInput = document.getElementById("question");
const runButton = document.getElementById("runButton");

const sqlOutput = document.getElementById("sqlOutput");
const resultsDiv = document.getElementById("results");

const backgroundVideo =
    document.getElementById("backgroundVideo");

const hoverCards =
    document.querySelectorAll(".hover-card");


/* =========================================
   BACKGROUND VIDEO
========================================= */

if (backgroundVideo) {

    backgroundVideo.play().catch(() => {

        console.log(
            "Video autoplay waiting for browser permission."
        );

    });

}


/* =========================================
   QUERY CARD HOVER
========================================= */

/*
    IMPORTANT:

    This only adds a class to the card's
    parent body.

    There is NO CSS changing the video
    when this happens.

    Therefore the background stays normal.
*/

hoverCards.forEach((card) => {

    card.addEventListener("mouseenter", () => {

        card.classList.add("is-hovered");

    });


    card.addEventListener("mouseleave", () => {

        card.classList.remove("is-hovered");

    });

});


/* =========================================
   RUN QUERY
========================================= */

runButton.addEventListener(
    "click",
    runQuery
);


async function runQuery() {

    const question =
        questionInput.value.trim();


    /* =====================================
       EMPTY QUESTION
    ====================================== */

    if (question === "") {

        resultsDiv.innerHTML =
            '<p class="error">Please enter a question.</p>';

        return;

    }


    /* =====================================
       DISABLE BUTTON
    ====================================== */

    runButton.disabled = true;


    runButton.innerHTML = `
        <span>Generating...</span>
        <span class="arrow">⟳</span>
    `;


    /* =====================================
       LOADING
    ====================================== */

    sqlOutput.textContent =
        "Qwen is generating SQL...";


    resultsDiv.innerHTML =
        '<p class="loading">Generating SQL and executing query...</p>';


    try {

        /* =================================
           SEND REQUEST TO FASTAPI
        ================================== */

        const response = await fetch(
            "http://127.0.0.1:8000/query",
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    question: question
                })
            }
        );


        /* =================================
           GET JSON RESPONSE
        ================================== */

        const data =
            await response.json();


        /* =================================
           BACKEND ERROR
        ================================== */

        if (data.error) {

            sqlOutput.textContent =
                "No SQL generated.";


            resultsDiv.innerHTML =
                `<p class="error">${escapeHTML(data.error)}</p>`;


            return;

        }


        /* =================================
           DISPLAY SQL
        ================================== */

        sqlOutput.textContent =
            data.sql;


        /* =================================
           DISPLAY RESULTS
        ================================== */

        displayResults(
            data.columns,
            data.results
        );

    }


    catch (error) {

        console.error(error);


        sqlOutput.textContent =
            "Request failed.";


        resultsDiv.innerHTML =
            `
            <p class="error">
                Could not connect to the FastAPI server.
            </p>
            `;

    }


    finally {

        /* ================================
           ENABLE BUTTON
        ================================= */

        runButton.disabled = false;


        runButton.innerHTML = `
            <span>Run Query</span>
            <span class="arrow">→</span>
        `;

    }

}


/* =========================================
   DISPLAY RESULTS
========================================= */

function displayResults(
    columns,
    rows
) {

    /* =====================================
       NO RESULTS
    ====================================== */

    if (
        !rows ||
        rows.length === 0
    ) {

        resultsDiv.innerHTML =
            "<p class='loading'>No results found.</p>";

        return;

    }


    let table = "<table>";


    /* =====================================
       TABLE HEADER
    ====================================== */

    table += "<thead>";

    table += "<tr>";


    for (const column of columns) {

        table += `
            <th>
                ${escapeHTML(column)}
            </th>
        `;

    }


    table += "</tr>";

    table += "</thead>";


    /* =====================================
       TABLE BODY
    ====================================== */

    table += "<tbody>";


    for (const row of rows) {

        table += "<tr>";


        for (const value of row) {

            table += `
                <td>
                    ${escapeHTML(value)}
                </td>
            `;

        }


        table += "</tr>";

    }


    table += "</tbody>";

    table += "</table>";


    /* =====================================
       INSERT TABLE
    ====================================== */

    resultsDiv.innerHTML =
        table;

}


/* =========================================
   HTML ESCAPE
========================================= */

function escapeHTML(value) {

    if (
        value === null ||
        value === undefined
    ) {

        return "";

    }


    return String(value)

        .replace(
            /&/g,
            "&amp;"
        )

        .replace(
            /</g,
            "&lt;"
        )

        .replace(
            />/g,
            "&gt;"
        )

        .replace(
            /"/g,
            "&quot;"
        )

        .replace(
            /'/g,
            "&#039;"
        );

}


/* =========================================
   ENTER KEY
========================================= */

questionInput.addEventListener(
    "keydown",
    function (event) {

        /*
            Enter = Run Query

            Shift + Enter = New Line
        */

        if (
            event.key === "Enter" &&
            !event.shiftKey
        ) {

            event.preventDefault();

            runQuery();

        }

    }
);