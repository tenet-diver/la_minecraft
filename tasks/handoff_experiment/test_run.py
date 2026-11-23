import tempfile
from pathlib import Path
import unittest

from run import evaluation_schedule, read_events, score, summarize, tasks, write_profiles


def inventory(time_ms, agent, has_target):
    return {"type": "inventory", "time_ms": time_ms, "agent": agent, "has_target": has_target}


class ScoreTests(unittest.TestCase):
    def test_single_holder_cannot_complete_both_objectives(self):
        result = score([inventory(1010, 0, True)], 1000, 5, 6000)
        self.assertEqual((result["status"], result["objectives"]), ("timeout", 1))

    def test_two_positive_snapshots_have_to_overlap(self):
        events = [inventory(1100, 0, True), inventory(1190, 1, True), inventory(1230, 0, False)]
        result = score(events, 1000, 5, 6000)
        self.assertEqual((result["status"], result["objectives"]), ("timeout", 1))

    def test_records_start_of_a_confirmed_joint_hold(self):
        events = [inventory(1100, 0, True), inventory(1400, 1, True)]
        result = score(events, 1000, 5, 1650)
        self.assertEqual((result["status"], result["completion_seconds"]), ("complete", .4))

    def test_late_inventory_event_cannot_complete(self):
        events = [inventory(1001, 0, True), inventory(6150, 1, True)]
        self.assertEqual(score(events, 1000, 5, 6500)["objectives"], 1)

    def test_disconnection_during_hold_is_an_error(self):
        events = [inventory(1100, 0, True), inventory(1200, 1, True),
                  {"type": "agent_exit", "time_ms": 1300}]
        self.assertEqual(score(events, 1000, 5, 1500)["status"], "error")


class DesignTests(unittest.TestCase):
    def test_schedule_pairs_conditions_on_each_scenario(self):
        suite = tasks()["held_out"]
        schedule = evaluation_schedule(suite, 5, 42)
        self.assertEqual(len(schedule), 30)
        self.assertEqual(schedule, evaluation_schedule(suite, 5, 42))
        for first, second in zip(schedule[::2], schedule[1::2]):
            self.assertEqual(first[:2], second[:2])
            self.assertEqual({first[2], second[2]}, {"baseline", "learned"})

    def test_report_keeps_errors_and_timeouts_distinct(self):
        planned = [("s", 1, "baseline"), ("s", 2, "baseline"), ("s", 3, "baseline")]
        rows = [{"scenario": "s", "arm": "baseline", "status": "timeout"},
                {"scenario": "s", "arm": "baseline", "status": "error"}]
        result = summarize(rows, planned)["s"]["baseline"]
        self.assertEqual((result["planned"], result["attempted"], result["timeout"], result["error"]),
                         (3, 2, 1, 1))
        self.assertEqual(result["completed_by_seconds"]["300"], 0)

    def test_treatment_only_adds_note_to_conversation_prompt(self):
        import json

        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            baseline = [json.loads(Path(p).read_text()) for p in write_profiles(folder, "model", "")]
            learned = [json.loads(Path(p).read_text()) for p in write_profiles(folder, "model", "Lesson.")]
            for control, treatment in zip(baseline, learned):
                self.assertEqual(treatment.pop("conversing"),
                                 control.pop("conversing") + "\nLessons from previous episodes:\nLesson.")
                self.assertEqual(control, treatment)

    def test_ignores_partially_written_event(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "events.jsonl"
            path.write_text('{"type":"ready"}\n{"type":')
            self.assertEqual(read_events(path), [{"type": "ready"}])


if __name__ == "__main__":
    unittest.main()
