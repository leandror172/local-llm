import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

// Word frequency counter — pure JDK, no Spring deps; compiles cleanly.
public class WordCounter {

    public static Map<String, Long> countWords(String text) {
        if (text == null || text.isBlank()) return Map.of();
        return List.of(text.trim().split("\\s+")).stream()
                .collect(Collectors.groupingBy(String::toLowerCase, Collectors.counting()));
    }

    public static void main(String[] args) {
        List<String> samples = new ArrayList<>();
        samples.add("to be or not to be");
        samples.add("the quick brown fox");
        for (String s : samples) {
            System.out.println(countWords(s));
        }
    }
}
