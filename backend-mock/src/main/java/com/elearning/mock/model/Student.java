package com.elearning.mock.model;

import jakarta.persistence.Entity;
import jakarta.persistence.Id;

@Entity
public class Student {
    @Id
    private String userId; // Legătura cu AI-ul vostru
    private String name;
    private String currentChapter;

    public Student() {}
    public Student(String userId, String name, String currentChapter) {
        this.userId = userId;
        this.name = name;
        this.currentChapter = currentChapter;
    }

    public String getUserId() { return userId; }
    public void setUserId(String userId) { this.userId = userId; }
    public String getCurrentChapter() { return currentChapter; }
    public void setCurrentChapter(String currentChapter) { this.currentChapter = currentChapter; }
}