fetch("/home/robert/Desktop/EggApp/temp_humidity_data.csv")
.then(response => response.text())
.then(data => {
    // Split the CSV data into rows
    const rows = data.split("\n");
    // Get the labels for the chart (the first row of the CSV file)
    const labels = rows[0].split(",");
    // Initialize an empty array for the chart data
    const chartData = [];
    // Loop through the rest of the rows in the CSV file
    for (let i = 1; i < rows.length - 1; i++) {
        // Split the current row into columns
        const columns = rows[i].split(",");
        // Push the data for the current row into the chartData array
        chartData.push({
            x: columns[0],
            y: columns[1]
        });
    }
    // Create the chart
    createChart(labels, chartData);
});

function createChart(labels, chartData) {
    // Get the canvas element
    const ctx = document.getElementById("tempChart").getContext("2d");
    // Create the chart
    const tempChart = new Chart(ctx, {
        type: "line",
        data: {
            labels: labels,
            datasets: [
                {
                    label: "Temperature (F)",
                    data: chartData,
                    backgroundColor: "rgba(255, 99, 132, 0.2)",
                    borderColor: "rgba(255, 99, 132, 1)",
                    borderWidth: 1
                }
            ]
        },
        options: {
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}