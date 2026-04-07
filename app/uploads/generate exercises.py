import json

# Mapping muscle group names to their IDs
muscle_id_map = {
    "Back": "03632f9c-8581-4a5e-b3da-3451ccb4b2bf",
    "Chest": "318783dd-51d9-4e7c-9ee9-7260cdfa8f1c",
    "Abs": "5becb596-87a2-4a0e-91b2-d793dc0949ed",
    "Biceps": "6d5c28cc-2706-4d2b-9a01-41da76b14068",
    "Calves": "9917f5db-9aa4-42b4-948f-fe393fc10f05",
    "Quads": "b43eeed8-f177-46a1-94ca-16d59096fa29",
    "Triceps": "bf10e3bf-fbdf-470e-bfcf-52b069f58bfa",
    "Shoulders": "e1595911-ce98-478f-a556-5d8961e2c7db",
}

# Exercise data
exercises = [
    ("Bench Press (Barbell)", "00251201-Barbell-Bench-Press_Chest.mp4", "Barbell", "Chest", ["Triceps", "Shoulders"]),
    ("Bench Press (Cable)", "01511201-Cable-Bench-Press_Chest.mp4", "Machine", "Chest", ["Triceps", "Shoulders"]),
    ("Bench Press (Dumbbell)", "02891201-Dumbbell-Bench-Press_Chest.mp4", "Dumbbell", "Chest", ["Triceps", "Shoulders"]),
    ("Bench Press (Smith Machine)", "07481201-Smith-Bench-Press_Chest.mp4", "Machine", "Chest", ["Triceps", "Shoulders"]),
    ("Butterfly (Pec Deck)", "10301201-Lever-Pec-Deck-Fly_Chest.mp4", "Machine", "Chest", []),
    ("Cable Fly Crossovers", "12691201-Cable-Standing-Up-Straight-Crossovers_Chest.mp4", "Machine", "Chest", []),
    ("Chest Dip (Assisted)", "00091201-Assisted-Chest-Dip-(kneeling)_Chest.mp4", "Machine", "Chest", []),
    ("Chest Fly (Dumbbell)", "03081201-Dumbbell-Fly_Chest.mp4", "Dumbbell", "Chest", []),
    ("Chest Fly (Machine)", "05961201-Lever-Seated-Fly_Chest.mp4", "Machine", "Chest", []),
    ("Chest Press (Machine)", "05771201-Lever-Chest-Press_Chest.mp4", "Machine", "Chest", []),
    ("Decline Bench Press (Barbell)", "03011201-Dumbbell-Decline-Bench-Press_Chest.mp4", "Barbell", "Chest", ["Triceps"]),
    ("Decline Bench Press (Dumbbell)", "13001201-Lever-Decline-Chest-Press_Chest-FIX.mp4", "Dumbbell", "Chest", ["Triceps"]),
    ("Decline Chest Fly (Dumbbell)", "03021201-Dumbbell-Decline-Fly_Chest.mp4", "Dumbbell", "Chest", []),
    ("Incline Bench Press (Barbell)", "00471201-Barbell-Incline-Bench-Press_Chest.mp4", "Barbell", "Chest", ["Triceps", "Shoulders"]),
    ("Incline Bench Press (Dumbbell)", "03141201-Dumbbell-Incline-Bench-Press_Chest.mp4", "Dumbbell", "Chest", ["Triceps", "Shoulders"]),
    ("Incline Bench Press (Smith Machine)", "07571201-Smith-Incline-Bench-Press_Chest.mp4", "Machine", "Chest", ["Triceps", "Shoulders"]),
    ("Incline Chest Press (Machine)", "14791201-Lever-Incline-Chest-Press_Chest.mp4", "Machine", "Chest", ["Triceps", "Shoulders"]),
    ("Incline Push Ups", "37851201-Incline-Push-Up-(on-box).mp4", "None", "Chest", []),
    ("Low Cable Fly Crossovers", "01791201-Cable-Low-Fly_Chest.mp4", "Machine", "Chest", []),
    ("Pullover (Dumbbell)", "03751201-Dumbbell-Pullover_Chest.mp4", "Dumbbell", "Chest", []),
    ("Pullover (Machine)", "22851201-Lever-Pullover-(plate-loaded)_Back.mp4", "Machine", "Chest", ["Back"]),
    ("Push Up", "06621201-Push-up-m_Chest.mp4", "None", "Chest", ["Triceps", "Shoulders"]),
    ("Seated Chest Flys (Cable)", "38691101-Cable-Seated-Chest-Fly_Chest_small.jpg", "Machine", "Chest", []),
]

# Convert to structured objects
exercise_objects = []
for name, pic, equipment, primary, secondary in exercises:
    exercise_objects.append({
        "name": name,
        "pic": pic,
        "tips": "",
        "equipment": equipment,
        "favourite": False,
        "muscle_id": muscle_id_map.get(primary, ""),
        "secondary_muscles": [muscle_id_map[m] for m in secondary if m in muscle_id_map],
    })

# Save as JSON
json_path = "exercises.json"
with open(json_path, "w") as f:
    json.dump(exercise_objects, f, indent=2)

json_path
