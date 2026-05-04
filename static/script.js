function editExpense(id, name, amount, date) {
  const updatedName = prompt("Edit expense name:", name);
  if (updatedName === null) return;

  const updatedAmount = prompt("Edit amount:", amount);
  if (updatedAmount === null) return;

  const updatedDate = prompt("Edit date (YYYY-MM-DD):", date);
  if (updatedDate === null) return;

  if (!updatedName.trim() || !updatedAmount.trim() || !updatedDate.trim()) {
    alert("All fields are required.");
    return;
  }

  const parsedAmount = parseFloat(updatedAmount);
  if (isNaN(parsedAmount) || parsedAmount <= 0) {
    alert("Amount must be a valid number greater than 0.");
    return;
  }

  const form = document.createElement("form");
  form.method = "POST";
  form.action = `/edit/${id}`;

  const fields = {
    name: updatedName.trim(),
    amount: parsedAmount.toFixed(2),
    date: updatedDate.trim(),
  };

  Object.keys(fields).forEach((key) => {
    const input = document.createElement("input");
    input.type = "hidden";
    input.name = key;
    input.value = fields[key];
    form.appendChild(input);
  });

  document.body.appendChild(form);
  form.submit();
}

function drawExpenseChart() {
  const canvas = document.getElementById("expenseChart");
  if (!canvas || typeof chartLabels === "undefined" || typeof chartValues === "undefined") return;

  const ctx = canvas.getContext("2d");
  const width = canvas.width;
  const height = canvas.height;

  ctx.clearRect(0, 0, width, height);

  if (!chartValues.length) {
    ctx.fillStyle = "#64748b";
    ctx.font = "16px Arial";
    ctx.fillText("No expense data to display.", 20, 40);
    return;
  }

  const maxValue = Math.max(...chartValues, 1);
  const barWidth = Math.max(30, (width - 80) / chartValues.length - 12);
  const chartBottom = height - 40;
  const chartTop = 30;
  const drawableHeight = chartBottom - chartTop;

  chartValues.forEach((value, index) => {
    const barHeight = (value / maxValue) * drawableHeight;
    const x = 50 + index * (barWidth + 12);
    const y = chartBottom - barHeight;

    ctx.fillStyle = "#3b82f6";
    ctx.fillRect(x, y, barWidth, barHeight);

    ctx.fillStyle = "#1f2937";
    ctx.font = "11px Arial";
    ctx.fillText(String(value), x, y - 6);

    const shortLabel = chartLabels[index].slice(5); // MM-DD
    ctx.fillText(shortLabel, x, chartBottom + 14);
  });

  ctx.strokeStyle = "#94a3b8";
  ctx.beginPath();
  ctx.moveTo(40, chartTop);
  ctx.lineTo(40, chartBottom);
  ctx.lineTo(width - 20, chartBottom);
  ctx.stroke();
}

document.addEventListener("DOMContentLoaded", drawExpenseChart);
