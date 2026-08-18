import java.io.InputStream;
import java.util.ArrayList;
import java.util.List;
import java.util.stream.Stream;

public class CsvParser {

    public static Stream<Record> parse(String input) {
        return parse(input, ',', '"');
    }

    public static Stream<Record> parse(InputStream input) {
        return parse(input, ',', '"');
    }

    public static Stream<Record> parse(String input, char delimiter, char quoteChar) {
        return parse(new java.io.StringReader(input), delimiter, quoteChar);
    }

    public static Stream<Record> parse(InputStream input, char delimiter, char quoteChar) {
        return parse(new java.io.InputStreamReader(input), delimiter, quoteChar);
    }

    private static Stream<Record> parse(java.io.Reader reader, char delimiter, char quoteChar) {
        List<String> errors = new ArrayList<>();
        try (java.util.Scanner scanner = new java.util.Scanner(reader)) {
            return scanner.useDelimiter("\n").tokens().map(line -> {
                try {
                    return parseLine(line, delimiter, quoteChar);
                } catch (Exception e) {
                    errors.add(e.getMessage());
                    return null;
                }
            }).filter(Objects::nonNull).collect(Collectors.toList()).stream();
        }
    }

    private static Record parseLine(String line, char delimiter, char quoteChar) throws Exception {
        List<String> fields = new ArrayList<>();
        StringBuilder field = new StringBuilder();
        boolean inQuote = false;

        for (char c : line.toCharArray()) {
            if (c == quoteChar) {
                inQuote = !inQuote;
            } else if (c == delimiter && !inQuote) {
                fields.add(field.toString());
                field.setLength(0);
            } else {
                field.append(c);
            }
        }

        fields.add(field.toString());

        return new Record(fields.toArray(new String[0]));
    }

    public static void main(String[] args) throws Exception {
        String csv = "name,age\nJohn Doe,\"25,000\"\nJane \"The Queen\" Smith,30";
        Stream<Record> stream = CsvParser.parse(csv);

        List<String> errors = new ArrayList<>();
        List<Record> records = stream.filter(Objects::nonNull).collect(Collectors.toList());

        for (String error : errors) {
            System.out.println("Error: " + error);
        }

        records.forEach(record -> System.out.println(record));
    }
}

record Record(String... fields) {}