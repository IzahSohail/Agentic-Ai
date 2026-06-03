import random
from dataclasses import dataclass, field

from flask import Flask, jsonify, render_template_string, request

DEFAULT_CHOICES = ["Yes", "No"]


@dataclass
class ChoiceStore:
    choices: list[str] = field(default_factory=lambda: DEFAULT_CHOICES.copy())

    def set_choices(self, values: list[str]) -> list[str]:
        _ = values
        self.choices = DEFAULT_CHOICES.copy()
        return self.choices

    def get_choices(self) -> list[str]:
        return self.choices

    def spin(self) -> str:
        return random.choice(self.choices)


app = Flask(__name__)
store = ChoiceStore()

PAGE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Picker Wheel</title>
  <style>
    :root {
      color-scheme: dark;
      --bg: #07111f;
      --panel: #0f1c2f;
      --panel-2: #13233a;
      --text: #f8fafc;
      --muted: #a5b4cc;
      --accent: #60a5fa;
      --accent-2: #22d3ee;
    }
    * {
      box-sizing: border-box;
    }
    body {
      margin: 0;
      min-height: 100vh;
      font-family: Arial, sans-serif;
      background: radial-gradient(circle at top, #153052 0%, var(--bg) 55%);
      color: var(--text);
      display: flex;
      justify-content: center;
      align-items: center;
      padding: 24px;
    }
    .app {
      width: min(1100px, 100%);
      display: grid;
      grid-template-columns: 340px 1fr;
      gap: 24px;
      align-items: center;
    }
    .panel {
      background: rgba(15, 28, 47, 0.92);
      border: 1px solid rgba(148, 163, 184, 0.18);
      border-radius: 24px;
      box-shadow: 0 30px 80px rgba(0, 0, 0, 0.35);
      backdrop-filter: blur(10px);
    }
    .controls {
      padding: 24px;
    }
    h1 {
      margin: 0 0 10px;
      font-size: 32px;
    }
    p {
      margin: 0 0 20px;
      color: var(--muted);
      line-height: 1.5;
    }
    .inputs {
      display: grid;
      gap: 12px;
      margin-bottom: 18px;
    }
    input {
      width: 100%;
      border: 1px solid rgba(148, 163, 184, 0.22);
      background: var(--panel-2);
      color: var(--text);
      padding: 13px 14px;
      border-radius: 14px;
      font-size: 16px;
      outline: none;
    }
    input:focus {
      border-color: var(--accent);
      box-shadow: 0 0 0 3px rgba(96, 165, 250, 0.18);
    }
    button {
      width: 100%;
      border: 0;
      border-radius: 14px;
      padding: 14px 16px;
      font-size: 16px;
      font-weight: 700;
      cursor: pointer;
      transition: transform 0.15s ease, opacity 0.15s ease;
    }
    button:hover {
      transform: translateY(-1px);
    }
    button:disabled {
      opacity: 0.65;
      cursor: not-allowed;
      transform: none;
    }
    .save-btn {
      margin-bottom: 10px;
      background: linear-gradient(135deg, var(--accent), var(--accent-2));
      color: #03101f;
    }
    .spin-btn {
      background: #f8fafc;
      color: #08111d;
    }
    .wheel-wrap {
      position: relative;
      display: flex;
      justify-content: center;
      align-items: center;
      padding: 32px;
      min-height: 680px;
    }
    canvas {
      width: min(620px, 100%);
      aspect-ratio: 1;
      max-width: 620px;
    }
    .pointer {
      position: absolute;
      top: 64px;
      width: 0;
      height: 0;
      border-left: 22px solid transparent;
      border-right: 22px solid transparent;
      border-top: 42px solid #f8fafc;
      filter: drop-shadow(0 10px 16px rgba(0, 0, 0, 0.35));
    }
    .result {
      position: absolute;
      bottom: 48px;
      text-align: center;
    }
    .result-label {
      color: var(--muted);
      font-size: 14px;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      margin-bottom: 8px;
    }
    .result-value {
      font-size: 38px;
      font-weight: 800;
      min-height: 46px;
    }
    @media (max-width: 900px) {
      .app {
        grid-template-columns: 1fr;
      }
      .wheel-wrap {
        min-height: 560px;
      }
      .pointer {
        top: 38px;
      }
      .result {
        bottom: 30px;
      }
    }
  </style>
</head>
<body>
  <div class="app">
    <section class="panel controls">
      <h1>Picker Wheel</h1>
      <p>Add up to 5 choices, save them, then spin the wheel.</p>
      <div class="inputs" id="inputs"></div>
      <button class="save-btn" id="saveButton">Save Choices</button>
      <button class="spin-btn" id="spinButton">Spin Wheel</button>
    </section>
    <section class="panel wheel-wrap">
      <div class="pointer"></div>
      <canvas id="wheel" width="620" height="620"></canvas>
      <div class="result">
        <div class="result-label">Result</div>
        <div class="result-value" id="result">-</div>
      </div>
    </section>
  </div>
  <script>
    const state = {
      choices: [],
      rotation: 0,
      spinning: false
    };

    const palette = ["#38bdf8", "#818cf8", "#f472b6", "#f59e0b", "#34d399"];
    const fullTurn = Math.PI * 2;
    const startAngle = -Math.PI / 2;
    const pointerAngle = Math.PI * 1.5;
    const canvas = document.getElementById("wheel");
    const ctx = canvas.getContext("2d");
    const inputsContainer = document.getElementById("inputs");
    const resultNode = document.getElementById("result");
    const saveButton = document.getElementById("saveButton");
    const spinButton = document.getElementById("spinButton");

    function normalizedChoices(values) {
      return ["Yes", "No"];
    }

    function getWheelSegments() {
      const totalSegments = 8;
      return Array.from({ length: totalSegments }, (_, index) => (index % 2 === 0 ? "Yes" : "No"));
    }

    function getSegmentAtPointer(rotation = state.rotation) {
      const segments = getWheelSegments();
      const slice = fullTurn / segments.length;
      const normalizedRotation = ((rotation % fullTurn) + fullTurn) % fullTurn;
      const relativeAngle = (pointerAngle - normalizedRotation - startAngle + fullTurn) % fullTurn;
      const index = Math.floor(relativeAngle / slice) % segments.length;
      return { label: segments[index], index };
    }

    function renderInputs() {
      inputsContainer.innerHTML = "";
      const values = [...state.choices];
      while (values.length < 5) {
        values.push("");
      }
      values.forEach((value, index) => {
        const input = document.createElement("input");
        input.type = "text";
        input.maxLength = 24;
        input.placeholder = `Choice ${index + 1}`;
        input.value = value;
        inputsContainer.appendChild(input);
      });
    }

    function drawWheel() {
      const segments = getWheelSegments();
      const count = segments.length;
      const center = canvas.width / 2;
      const radius = 250;
      const slice = fullTurn / count;
      const fontSize = count >= 12 ? 18 : 24;

      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.save();
      ctx.translate(center, center);
      ctx.rotate(state.rotation);

      for (let i = 0; i < count; i += 1) {
        const start = startAngle + i * slice;
        const end = start + slice;
        ctx.beginPath();
        ctx.moveTo(0, 0);
        ctx.arc(0, 0, radius, start, end);
        ctx.closePath();
        ctx.fillStyle = palette[i % palette.length];
        ctx.fill();

        ctx.save();
        ctx.rotate(start + slice / 2);
        ctx.textAlign = "right";
        ctx.fillStyle = "#03101f";
        ctx.font = `bold ${fontSize}px Arial`;
        ctx.fillText(segments[i], radius - 18, 8);
        ctx.restore();
      }

      ctx.beginPath();
      ctx.arc(0, 0, radius + 2, 0, Math.PI * 2);
      ctx.strokeStyle = "rgba(248, 250, 252, 0.9)";
      ctx.lineWidth = 8;
      ctx.stroke();

      ctx.beginPath();
      ctx.arc(0, 0, 38, 0, Math.PI * 2);
      ctx.fillStyle = "#f8fafc";
      ctx.fill();

      ctx.restore();
    }

    async function loadChoices() {
      const response = await fetch("/api/choices");
      const data = await response.json();
      state.choices = normalizedChoices(data.choices || []);
      renderInputs();
      drawWheel();
    }

    async function saveChoices() {
      const values = [...inputsContainer.querySelectorAll("input")].map((input) => input.value);
      const response = await fetch("/api/choices", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ choices: values })
      });
      const data = await response.json();
      state.choices = normalizedChoices(data.choices || []);
      renderInputs();
      drawWheel();
      resultNode.textContent = "-";
    }

    function animateSpin(targetRotation) {
      const start = state.rotation;
      const startTime = performance.now();
      const duration = 4200;

      function step(now) {
        const progress = Math.min((now - startTime) / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 4);
        state.rotation = start + (targetRotation - start) * eased;
        drawWheel();
        if (progress < 1) {
          requestAnimationFrame(step);
        } else {
          state.rotation = ((targetRotation % fullTurn) + fullTurn) % fullTurn;
          state.spinning = false;
          spinButton.disabled = false;
          saveButton.disabled = false;
          resultNode.textContent = getSegmentAtPointer(state.rotation).label;
          drawWheel();
        }
      }

      requestAnimationFrame(step);
    }

    async function spinWheel() {
      if (state.spinning) {
        return;
      }
      state.spinning = true;
      spinButton.disabled = true;
      saveButton.disabled = true;
      resultNode.textContent = "Spinning...";

      const response = await fetch("/api/spin", { method: "POST" });
      const data = await response.json();
      const segments = getWheelSegments();
      const matchingIndexes = [];
      segments.forEach((segment, index) => {
        if (segment === data.winner) {
          matchingIndexes.push(index);
        }
      });
      const winnerIndex = matchingIndexes[Math.floor(Math.random() * matchingIndexes.length)];
      const slice = fullTurn / segments.length;
      const winnerCenter = startAngle + winnerIndex * slice + slice / 2;
      const extraTurns = fullTurn * (6 + Math.random() * 2);
      const finalAngle = pointerAngle - winnerCenter;
      const baseRotation = ((state.rotation % fullTurn) + fullTurn) % fullTurn;
      const targetRotation = state.rotation + extraTurns + ((finalAngle - baseRotation + fullTurn) % fullTurn);

      animateSpin(targetRotation);
    }

    saveButton.addEventListener("click", saveChoices);
    spinButton.addEventListener("click", spinWheel);
    loadChoices();
  </script>
</body>
</html>
"""


@app.get("/")
def index() -> str:
    return render_template_string(PAGE)


@app.get("/api/choices")
def get_choices():
    return jsonify({"choices": store.set_choices([])})


@app.post("/api/choices")
def update_choices():
    payload = request.get_json(silent=True) or {}
    values = payload.get("choices", [])
    if not isinstance(values, list):
        values = []
    choices = store.set_choices([str(value) for value in values])
    return jsonify({"choices": choices})


@app.post("/api/spin")
def spin():
    return jsonify({"winner": store.spin()})


def main() -> None:
    app.run(debug=True)


if __name__ == "__main__":
    main()
