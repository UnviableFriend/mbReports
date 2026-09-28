(() => {
    document.querySelectorAll("time[datetime]").forEach((time) => {
        const date = new Date(time.dateTime);

        if (Number.isNaN(date.getTime())) return;

        time.textContent = new Intl.DateTimeFormat(undefined, {
            dateStyle: "medium",
            timeStyle: "short"
        }).format(date);
    });

    const input = document.getElementById("table-filter");
    const table = document.getElementById("report-table");
    const count = document.getElementById("row-count");

    if (!input || !table) return;

    const rows = Array.from(table.querySelectorAll("tbody tr"));

    function update() {
        const query = input.value.trim().toLowerCase();
        let visible = 0;

        for (const row of rows) {
            const matches = !query || row.textContent.toLowerCase().includes(query);
            row.hidden = !matches;
            if (matches) visible++;
        }

        if (count) {
            count.textContent = `${visible} of ${rows.length} rows`;
        }
    }

    input.addEventListener("input", update);
    update();
})();
