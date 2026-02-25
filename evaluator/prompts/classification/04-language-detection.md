---
id: cls-04-language-detection
domain: classification
difficulty: medium
timeout: 120
description: Programming language detection from a code snippet
---

Identify the programming language of the following code snippet.

Categories: python, javascript, typescript, java, go, rust, cpp, csharp, ruby, php, other

Code snippet:
```
func fetchUsers(ctx context.Context, db *sql.DB) ([]User, error) {
    rows, err := db.QueryContext(ctx, "SELECT id, name, email FROM users WHERE active = $1", true)
    if err != nil {
        return nil, fmt.Errorf("query users: %w", err)
    }
    defer rows.Close()
    var users []User
    for rows.Next() {
        var u User
        if err := rows.Scan(&u.ID, &u.Name, &u.Email); err != nil {
            return nil, err
        }
        users = append(users, u)
    }
    return users, rows.Err()
}
```

Respond with JSON: {"category": "<language>", "confidence": <0.0-1.0>, "reasoning": "<one sentence citing specific language features>"}
