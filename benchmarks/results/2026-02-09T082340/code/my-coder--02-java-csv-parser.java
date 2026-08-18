import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.function.Function;
import java.util.stream.Collectors;
import java.util.stream.Stream;

public class CsvParser {

    public record Row(String[] fields) {}

    private final char delimiter;
    private final char quoteChar;

    public CsvParser(char delimiter, char quoteChar) {
        this.delimiter = delimiter;
        this.quoteChar = quoteChar;
    }

    public Stream<Row> parse(InputStream inputStream) {
        return new BufferedReader(new InputStreamReader(inputStream, StandardCharsets.UTF_8))
                .lines()
                .flatMap(line -> parseLine(line).stream());
    }

    public Stream<Row> parse(String input) {
        return Arrays.stream(input.split("\n"))
                .flatMap(line -> parseLine(line).stream());
    }

    private List<String> parseLine(String line) {
        List<String> fields = new ArrayList<>();
        StringBuilder field = new StringBuilder();
        boolean inQuote = false;

        for (char c : line.toCharArray()) {
            if (c == quoteChar) {
                if (inQuote && field.length() > 0 && field.charAt(field.length() - 1) == quoteChar) {
                    // Escaped quote
                    field.setLength(field.length() - 1);
                } else {
                    inQuote = !inQuote;
                }
            } else if (c == delimiter && !inQuote) {
                fields.add(field.toString());
                field.setLength(0);
            } else {
                field.append(c);
            }
        }

        if (!field.isEmpty()) {
            fields.add(field.toString());
        }

        return fields.stream()
                .map(this::unescapeQuotes)
                .collect(Collectors.toList());
    }

    private String unescapeQuotes(String field) {
        if (field.startsWith("\"") && field.endsWith("\"")) {
            return field.substring(1, field.length() - 1).replace("\"\"", "\"");
        }
        return field;
    }

    public static void main(String[] args) throws Exception {
        CsvParser parser = new CsvParser(',', '"');

        String sampleCsv = "id,name,description\n" +
                "1,\"John Doe\",This is a \"quoted\" string.\n" +
                "2,Jane Smith,\n" +
                "3,Bob,,\n" +
                "4,,Invalid row";

        Stream<Row> rows = parser.parse(sampleCsv);

        List<String> errors = new ArrayList<>();
        rows.onClose(() -> {
            System.out.println("Parsing errors:");
            errors.forEach(System.err::println);
        });

        rows.filter(row -> !row.fields()[2].isEmpty())
                .forEach(row -> System.out.println("ID: " + row.fields()[0] + ", Name: " + row.fields()[1]));

        // Simulate parsing error
        parser.parse(new ByteArrayInputStream("id,name\n1,John Doe".getBytes(StandardCharsets.UTF_8)))
              .onClose(() -> {
                  errors.add("Malformed row at line 2");
              });
    }
}