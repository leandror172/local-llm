# Test 1: Spring Boot REST API

Create a Spring Boot REST API application in a `springboot-api/` directory with the following:

## Requirements

**Entities:**
- `User` — fields: id (Long, auto-generated), name (String), email (String, unique)
- `Todo` — fields: id (Long, auto-generated), title (String), description (String), completed (boolean, default false), createdAt (LocalDateTime, auto-set)
- Relationship: A User has many Todos. Each Todo belongs to one User.

**Endpoints:**
- `GET /api/users` — list all users
- `POST /api/users` — create a user (accepts JSON body with name and email)
- `GET /api/users/{id}` — get a single user with their todos
- `POST /api/users/{id}/todos` — create a todo for a user
- `PATCH /api/todos/{id}` — toggle a todo's completed status
- `DELETE /api/todos/{id}` — delete a todo

**Technical:**
- Spring Boot 3.x with Java 17+
- Spring Data JPA with H2 in-memory database
- Include `application.properties` with H2 console enabled at `/h2-console`
- Include a Maven wrapper (`mvnw`) or at minimum a `pom.xml`
- Return proper HTTP status codes (201 for creation, 404 for not found, etc.)
- Use constructor injection (no `@Autowired` on fields)
