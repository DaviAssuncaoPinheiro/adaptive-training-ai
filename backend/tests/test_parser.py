"""Quick test for the JSON parser and validator."""
from backend.services.llm_service import extract_json_from_response, validate_microcycle_structure

# Simular resposta do LLM com markdown wrapping
raw = '```json\n{"workouts": [{"session_name": "Treino A", "day_of_week": 1, "exercises": [{"exercise_name": "Supino Reto", "target_sets": 4, "target_reps": "8-12", "target_rpe": 7, "rest_seconds": 90}]}], "ai_justification": "Teste de validacao.", "max_weekly_sets_per_muscle": 16, "max_rpe_cap": 8}\n```'

parsed = extract_json_from_response(raw)
validated = validate_microcycle_structure(parsed)
print(f"Parser OK. Sessions: {len(validated['workouts'])}")
print(f"Justification: {validated['ai_justification'][:30]}")
print(f"Safety caps: sets={validated['max_weekly_sets_per_muscle']}, rpe={validated['max_rpe_cap']}")

# Test with raw JSON (no markdown)
raw2 = '{"workouts": [{"session_name": "B", "day_of_week": 2, "exercises": [{"exercise_name": "Agachamento", "target_sets": 3, "target_reps": "6-8", "target_rpe": 8, "rest_seconds": 120}]}], "ai_justification": "Foco em forca.", "max_weekly_sets_per_muscle": 12, "max_rpe_cap": 9}'
parsed2 = extract_json_from_response(raw2)
validated2 = validate_microcycle_structure(parsed2)
print(f"Raw JSON OK. Sessions: {len(validated2['workouts'])}")

print("\nAll parser tests passed.")
