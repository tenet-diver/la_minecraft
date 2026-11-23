# MineCollab coordination handoff experiment

The runner collects eight practice episodes, updates one team note after each, and freezes it before evaluation. Fresh teams play the same three held-out scenarios with and without that note. The default is five repetitions per condition per scenario (30 evaluation episodes).

Each episode starts in a clean, deterministic Minecraft kitchen with one crafting table and split inventories. Each agent sees its own target and the other agent's recipe. Both can share ingredients, recipes, and dishes. The benchmark measures transfer of coordination procedures. Vanilla recipes may already be familiar to the bots' model.

## Run

Use Linux or macOS with Python 3.11+, Node.js, Java 21, and the official Minecraft Java 1.21.6 server JAR. Set `OPENAI_API_KEY` or use the fork's ignored `keys.json` for the intended OpenAI API organization. The live runner uses the Responses API for bot turns and note updates. The local Minecraft server binds to loopback and uses offline bot names.

Install dependencies with `npm install`. For headless Linux without graphics build dependencies, use `npm install --ignore-scripts && npx --no-install patch-package`. Rendering and vision are disabled in this experiment.

```sh
python3 -m unittest discover -s tasks/handoff_experiment -p 'test_*.py'
python3 tasks/handoff_experiment/run.py --plan --output experiments/handoff-plan

# After reviewing and accepting https://aka.ms/MinecraftEULA
python3 tasks/handoff_experiment/run.py \
  --server-jar /path/to/server-1.21.6.jar --accept-minecraft-eula \
  --scripted-smoke --output experiments/handoff-smoke

python3 tasks/handoff_experiment/run.py \
  --server-jar /path/to/server-1.21.6.jar --accept-minecraft-eula \
  --model gpt-5.4-mini --output experiments/handoff-live
```

The plan and scripted smoke modes make zero API calls. The smoke test runs three real Minecraft episodes using server console commands: both dishes on one bot (1/2), both dishes with their assigned owners (2/2), and a fresh world (0/2). Use a new output directory on each invocation. Use `--repetitions 1` for a smaller live check with eight practice and six evaluation episodes. The default suite can take several hours if tasks time out.

## Read results

The clock starts when both agents have received their starting inventories. Full completion requires both agents to hold their assigned dishes together for an observed 250 ms, allowing for small packet timing differences. Completion time is the beginning of that confirmed hold. Timeouts retain partial scores. The runner records infrastructure errors separately and stops.

- `manifest.json` records the commit, model, scenario inputs, seed, run order, and server JAR hash.
- `practice.json`, each episode's `updated_note.md`, and `frozen_note.md` preserve the intervention.
- `evaluation.json` records each result, elapsed time, first message and relevant commands, and model call usage and latency.
- `summary.json` reports planned and attempted runs, completions, timeouts, errors, and cumulative completions every 30 seconds per scenario and condition. Keep valid timeouts in completion-rate denominators. Report errors and unattempted runs separately.
- Each episode retains raw events and both process logs. Its disposable world is removed after shutdown.

The primary comparison is full completion by 300 seconds. The small sample is exploratory. A future length-matched advice condition could test whether the learned procedures outperform general teamwork advice.
