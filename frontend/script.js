const API_URL = "https://nl-sql-query-builder.onrender.com/query";


// ==========================================
// ELEMENTS
// ==========================================

const questionInput = document.getElementById("question");
const runButton = document.getElementById("runButton");

const sqlOutput = document.getElementById("sqlOutput");
const resultsContainer = document.getElementById("results");


// ==========================================
// ESCAPE HTML
// ==========================================

function escapeHTML(value) {

    const div = document.createElement("div");

    div.textContent = value;

    return div.innerHTML;
}


// ==========================================
// RUN QUERY
// ==========================================

async function runQuery() {

    const question = questionInput.value.trim();


    // ==========================================
    // CHECK EMPTY QUESTION
    // ==========================================

    if (!question) {

        resultsContainer.innerHTML =
            "<p>Please enter a question.</p>";

        return;
    }


    // ==========================================
    // LOADING STATE
    // ==========================================

    runButton.disabled = true;

    runButton.innerHTML = `
        <span>Running...</span>
        <span class="arrow">→</span>
    `;

    sqlOutput.textContent = "Generating SQL...";

    resultsContainer.innerHTML =
        "<p>Waiting for database results...</p>";


    try {

        // ==========================================
        // SEND REQUEST TO RENDER
        // ==========================================

        const response = await fetch(API_URL, {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                question: question
            })
        });


        // ==========================================
        // GET RESPONSE
        // ==========================================

        const data = await response.json();


        // ==========================================
        // CHECK API ERROR
        // ==========================================

        if (!response.ok || data.error) {

            sqlOutput.textContent =
                "No SQL generated.";

            resultsContainer.innerHTML =
                `<p>${escapeHTML(
                    data.error || "Something went wrong."
                )}</p>`;

            return;
        }


        // ==========================================
        // SHOW GENERATED SQL
        // ==========================================

        sqlOutput.textContent = data.sql;


        // ==========================================
        // CHECK RESULTS
        // ==========================================

        if (!data.results || data.results.length === 0) {

            resultsContainer.innerHTML =
                "<p>No results found.</p>";

            return;
        }


        // ==========================================
        // CREATE RESULT TABLE
        // ==========================================

        let tableHTML = "<table>";


        // ==========================================
        // TABLE HEADER
        // ==========================================

        tableHTML += "<thead>";

        tableHTML += "<tr>";


        for (const column of data.columns) {

            tableHTML += `
                <th>
                    ${escapeHTML(column)}
                </th>
            `;
        }


        tableHTML += "</tr>";

        tableHTML += "</thead>";


        // ==========================================
        // TABLE BODY
        // ==========================================

        tableHTML += "<tbody>";


        for (const row of data.results) {

            tableHTML += "<tr>";


            for (const value of row) {

                tableHTML += `
                    <td>
                        ${escapeHTML(value)}
                    </td>
                `;
            }


            tableHTML += "</tr>";
        }


        tableHTML += "</tbody>";

        tableHTML += "</table>";


        // ==========================================
        // DISPLAY TABLE
        // ==========================================

        resultsContainer.innerHTML = tableHTML;


    } catch (error) {

        console.error("Frontend error:", error);


        sqlOutput.textContent =
            "Unable to generate SQL.";


        resultsContainer.innerHTML = `
            <p>
                Unable to connect to the backend.
                Please try again.
            </p>
        `;


    } finally {

        // ==========================================
        // RESTORE BUTTON
        // ==========================================

        runButton.disabled = false;

        runButton.innerHTML = `
            <span>Run Query</span>
            <span class="arrow">→</span>
        `;
    }
}


// ==========================================
// BUTTON CLICK
// ==========================================

runButton.addEventListener(
    "click",
    runQuery
);


// ==========================================
// ENTER KEY
// ==========================================

questionInput.addEventListener(
    "keydown",
    function (event) {

        if (
            event.key === "Enter" &&
            !event.shiftKey
        ) {

            event.preventDefault();

            runQuery();
        }
    }
);


// ==========================================
// HOVER EFFECT
// ==========================================

const hoverCards =
    document.querySelectorAll(".hover-card");


hoverCards.forEach(function (card) {

    card.addEventListener(
        "mouseenter",
        function () {

            card.classList.add("hovered");
        }
    );


    card.addEventListener(
        "mouseleave",
        function () {

            card.classList.remove("hovered");
        }
    );
});