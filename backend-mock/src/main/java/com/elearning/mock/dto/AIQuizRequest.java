package com.elearning.mock.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

public class AIQuizRequest {

    @JsonProperty("user_id") // Aceasta linie forțează Java să scrie "user_id" în JSON
    private String userId;

    @JsonProperty("lesson_type")
    private String lessonType;

    @JsonProperty("lesson_text")
    private String lessonText;

    // Getters și Setters (pot rămâne cu numele de Java)
    public String getUserId() { return userId; }
    public void setUserId(String userId) { this.userId = userId; }

    public String getLessonType() { return lessonType; }
    public void setLessonType(String lessonType) { this.lessonType = lessonType; }

    public String getLessonText() { return lessonText; }
    public void setLessonText(String lessonText) { this.lessonText = lessonText; }
}