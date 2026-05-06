-- Mock pentru dificultate EASY (scor sub 0.4)
INSERT INTO student_mastery (
        user_id,
        topic_name,
        mastery_score,
        wrong_answers_count
    )
VALUES (
        '75d5ca88-a984-4d3e-b2fb-73461752a4ad',
        'Biologie',
        0.2,
        5
    ) ON CONFLICT (user_id, topic_name) DO
UPDATE
SET mastery_score = EXCLUDED.mastery_score;
-- Mock pentru dificultate HARD (scor peste 0.7)
INSERT INTO student_mastery (
        user_id,
        topic_name,
        mastery_score,
        wrong_answers_count
    )
VALUES ('LIPESTE_USER_ID_AICI', 'Informatica', 0.85, 1) ON CONFLICT (user_id, topic_name) DO
UPDATE
SET mastery_score = EXCLUDED.mastery_score;