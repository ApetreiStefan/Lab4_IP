package com.elearning.mock.controller;

import com.elearning.mock.service.AIIntegrationService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/mock-backend")
public class IntegrationController {

    @Autowired
    private AIIntegrationService aiIntegrationService;

    // Am adăugat @RequestParam pentru a prelua materia direct din URL
    @PostMapping("/trigger-quiz/{userId}")
    public String triggerQuizForStudent(
            @PathVariable String userId,
            @RequestParam String lessonType,
            @RequestBody String lessonText) {

        // Acum trimitem mai departe exact materia pe care ne-o cere Frontend-ul
        return aiIntegrationService.requestPopQuizFromAI(userId, lessonType, lessonText);
    }
}