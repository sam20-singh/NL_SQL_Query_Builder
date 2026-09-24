const questionInput = document.getElementById("question");
const runButton = document.getElementById("runButton");
const sqlOutput = document.getElementById("sqlOutput");
const resultsDiv = document.getElementById("results");


runButton.addEventListener("click", runQuery);


async function runQuery() {

    const question = questionInput.value.trim();


    if (question === "") {

        resultsDiv.innerHTML =
            '<p class="error">Please enter a question.</p>';

        return;
    }


    runButton.disabled = true;


    runButton.innerHTML = `
        <span>Generating...</span>
        <span class="arrow">⟳</span>
    `;


    sqlOutput.textContent = "Generating SQL...";


    resultsDiv.innerHTML =
        '<p class="loading">Qwen is generating and executing your query...</p>';


    try {

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


        const data = await response.json();


        if (data.error) {

            sqlOutput.textContent = "No SQL generated.";

            resultsDiv.innerHTML =
                `<p class="error">${data.error}</p>`;

            return;
        }


        // Display generated SQL
        sqlOutput.textContent = data.sql;


        // Display database results
        displayResults(
            data.columns,
            data.results
        );


    } catch (error) {

        sqlOutput.textContent = "Request failed.";

        resultsDiv.innerHTML =
            '<p class="error">Could not connect to the FastAPI server.</p>';

        console.error(error);

    } finally {

        runButton.disabled = false;

        runButton.innerHTML = `
            <span>Run Query</span>
            <span class="arrow">→</span>
        `;
    }
}



function displayResults(columns, rows) {

    if (rows.length === 0) {

        resultsDiv.innerHTML =
            "<p>No results found.</p>";

        return;
    }


    let table = "<table>";


    // Create table header
    table += "<thead>";
    table += "<tr>";


    for (const column of columns) {

        table += `<th>${column}</th>`;
    }


    table += "</tr>";
    table += "</thead>";


    // Create table body
    table += "<tbody>";


    for (const row of rows) {

        table += "<tr>";


        for (const value of row) {

            table += `<td>${value}</td>`;
        }


        table += "</tr>";
    }


    table += "</tbody>";
    table += "</table>";


    // Put table into webpage
    resultsDiv.innerHTML = table;
}