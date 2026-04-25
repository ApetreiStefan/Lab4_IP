package com.elearning.mock.service;

import com.elearning.mock.dto.AIQuizRequest;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;
import org.springframework.http.ResponseEntity;

@Service
public class AIIntegrationService {

    private final RestTemplate restTemplate;
    // URL-ul FastAPI-ului vostru
    private static final String AI_SERVICE_URL = "http://localhost:8000/db-pop-quiz";

    public AIIntegrationService() {
        this.restTemplate = new RestTemplate();
    }

    public String requestPopQuizFromAI(String userId, String lessonType, String lessonText) {
        AIQuizRequest requestPayload = new AIQuizRequest();
        requestPayload.setUserId(userId);
        requestPayload.setLessonType(lessonType);
        requestPayload.setLessonText(lessonText);

        try {
            ResponseEntity<String> response = restTemplate.postForEntity(AI_SERVICE_URL, requestPayload, String.class);
            return response.getBody();
        } catch (Exception e) {
            return "{\"error\": \"Eroare la comunicarea cu AI: " + e.getMessage() + "\"}";
        }
    }
}