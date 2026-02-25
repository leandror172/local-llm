package com.example.demo;

import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

// Spring Boot REST controller — typical LLM output; compiles only with Spring on classpath.
// Phase 1 validator expects: missing_dependency warnings, zero real errors → score 3.
@RestController
@RequestMapping("/users")
public class UserController {

    private final UserService userService;

    public UserController(UserService userService) {
        this.userService = userService;
    }

    @GetMapping("/{id}")
    public ResponseEntity<String> getUser(@PathVariable Long id) {
        return ResponseEntity.ok(userService.findById(id).toString());
    }

    @PostMapping
    public ResponseEntity<String> createUser(@Valid @RequestBody String body) {
        return ResponseEntity.ok(userService.save(body).toString());
    }
}
