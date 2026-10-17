# Sort modes

The profiles below are defaults. A domain model may supply an override, but
the selected weights and model version must appear in the result.

All profiles use the dimensions from [priority-model.md](priority-model.md).
Weights sum to 1.0.

| Mode | Main use |
| --- | --- |
| `default` | Balance exam value, weakness, risk, dependencies, and coverage. |
| `exam` | Prefer high-yield and frequently tested cards. |
| `weakness` | Prefer current weakness and recent exam errors. |
| `risk` | Prefer errors, confusions, and coverage risks. |
| `prerequisite` | Prefer cards that unlock many downstream cards. |
| `tonight` | Use a bounded session queue with a stable full ranking underneath. |

~~~json
{
  "default": {
    "exam_importance": 0.16,
    "error_risk": 0.14,
    "dependency_weight": 0.12,
    "user_weakness": 0.16,
    "recent_exam_errors": 0.12,
    "coverage_gap": 0.10,
    "confusion_density": 0.08,
    "recall_difficulty": 0.06,
    "question_frequency": 0.06
  },
  "exam": {
    "exam_importance": 0.22,
    "error_risk": 0.14,
    "dependency_weight": 0.12,
    "user_weakness": 0.14,
    "recent_exam_errors": 0.14,
    "coverage_gap": 0.06,
    "confusion_density": 0.04,
    "recall_difficulty": 0.02,
    "question_frequency": 0.12
  },
  "weakness": {
    "exam_importance": 0.05,
    "error_risk": 0.15,
    "dependency_weight": 0.08,
    "user_weakness": 0.25,
    "recent_exam_errors": 0.18,
    "coverage_gap": 0.12,
    "confusion_density": 0.08,
    "recall_difficulty": 0.07,
    "question_frequency": 0.02
  },
  "risk": {
    "exam_importance": 0.08,
    "error_risk": 0.25,
    "dependency_weight": 0.06,
    "user_weakness": 0.10,
    "recent_exam_errors": 0.12,
    "coverage_gap": 0.14,
    "confusion_density": 0.18,
    "recall_difficulty": 0.05,
    "question_frequency": 0.02
  },
  "prerequisite": {
    "exam_importance": 0.12,
    "error_risk": 0.10,
    "dependency_weight": 0.30,
    "user_weakness": 0.08,
    "recent_exam_errors": 0.06,
    "coverage_gap": 0.12,
    "confusion_density": 0.05,
    "recall_difficulty": 0.05,
    "question_frequency": 0.12
  },
  "tonight": {
    "exam_importance": 0.10,
    "error_risk": 0.15,
    "dependency_weight": 0.15,
    "user_weakness": 0.20,
    "recent_exam_errors": 0.15,
    "coverage_gap": 0.10,
    "confusion_density": 0.05,
    "recall_difficulty": 0.08,
    "question_frequency": 0.02
  }
}
~~~
