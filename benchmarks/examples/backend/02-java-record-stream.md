---
id: ex-02-java-record-stream
category: backend
type: few-shot-example
demonstrates: records, Stream API, complete main(), idiomatic Java 21+
---

## Task

Filter and transform a product list using records and streams.

## Input

Given a list of products with name, price, and category, write a Java program that filters products under $50 in the "electronics" category and returns their names in uppercase, sorted alphabetically.

## Output

```java
import java.util.List;

record Product(String name, double price, String category) {}

public class ProductFilter {
    public static List<String> cheapElectronics(List<Product> products) {
        return products.stream()
                .filter(p -> p.category().equals("electronics"))
                .filter(p -> p.price() < 50.0)
                .map(p -> p.name().toUpperCase())
                .sorted()
                .toList();
    }

    public static void main(String[] args) {
        var products = List.of(
                new Product("USB Cable", 12.99, "electronics"),
                new Product("Notebook", 4.50, "office"),
                new Product("Mouse Pad", 8.99, "electronics"),
                new Product("Headphones", 79.99, "electronics"),
                new Product("SD Card", 24.99, "electronics")
        );

        List<String> result = cheapElectronics(products);
        result.forEach(System.out::println);
    }
}
```
