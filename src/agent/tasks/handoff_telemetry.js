import { appendFileSync, existsSync } from 'node:fs';
import { join } from 'node:path';

const directory = process.env.MINECOLLAB_HANDOFF_DIR;

export function handoffEvent(type, fields = {}) {
    if (!directory) return;
    appendFileSync(join(directory, 'events.jsonl'),
        JSON.stringify({ type, time_ms: Date.now(), ...fields }) + '\n');
}

export async function prepareHandoffAgent(agent, data) {
    if (!directory) throw new Error('Run handoff scenarios with tasks/handoff_experiment/run.py');
    const id = agent.count_id;
    const expected = data.initial_inventory[String(id)];
    const target = data.target[id];
    let previous;
    function sampleInventory() {
        const items = {};
        for (const item of agent.bot.inventory.items()) {
            items[item.name] = (items[item.name] || 0) + item.count;
        }
        const snapshot = JSON.stringify(items);
        if (snapshot !== previous) {
            handoffEvent('inventory', { agent: id, items, has_target: (items[target] || 0) >= 1 });
            previous = snapshot;
        }
        return Object.keys(items).length === Object.keys(expected).length &&
            Object.entries(expected).every(([name, count]) => items[name] === count);
    }

    handoffEvent('spawned', { agent: id });
    const deadline = Date.now() + 60000;
    let ready = false;
    while (Date.now() < deadline) {
        if (sampleInventory() && !ready) {
            handoffEvent('ready', { agent: id });
            ready = true;
        }
        if (ready && existsSync(join(directory, 'release'))) {
            // Observe each inventory update and keep a periodic check for slot changes.
            agent.bot.inventory.on('updateSlot', sampleInventory);
            setInterval(sampleInventory, 250).unref();
            return;
        }
        await new Promise(resolve => setTimeout(resolve, 50));
    }
    throw new Error('Timed out waiting for the experiment runner to release the task');
}
