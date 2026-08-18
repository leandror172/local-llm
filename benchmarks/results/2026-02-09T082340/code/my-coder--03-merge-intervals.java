import java.util.*;

public class IntervalMerger {

    public static <T extends Comparable<T>> List<Interval<T>> mergeIntervals(List<Interval<T>> intervals) {
        if (intervals == null || intervals.isEmpty()) {
            return new ArrayList<>();
        }

        // Sort intervals based on start value
        Collections.sort(intervals, Comparator.comparing(Interval::getStart));

        List<Interval<T>> merged = new ArrayList<>();
        Interval<T> current = intervals.get(0);

        for (int i = 1; i < intervals.size(); i++) {
            Interval<T> next = intervals.get(i);
            if (current.getEnd().compareTo(next.getStart()) >= 0) {
                // Overlapping intervals, merge them
                current = new Interval<>(current.getStart(), max(current.getEnd(), next.getEnd()));
            } else {
                // No overlap, add the current interval to merged list and update current
                merged.add(current);
                current = next;
            }
        }

        // Add the last interval
        merged.add(current);

        return merged;
    }

    private static <T extends Comparable<T>> T max(T a, T b) {
        if (a.compareTo(b) > 0) {
            return a;
        } else {
            return b;
        }
    }

    public static void main(String[] args) {
        // Test cases
        List<Interval<Integer>> intervals1 = Arrays.asList(new Interval<>(1, 3), new Interval<>(2, 6), new Interval<>(8, 10), new Interval<>(15, 18));
        System.out.println(mergeIntervals(intervals1)); // Expected: [1, 6], [8, 10], [15, 18]

        List<Interval<Integer>> intervals2 = Arrays.asList(new Interval<>(1, 4), new Interval<>(2, 3));
        System.out.println(mergeIntervals(intervals2)); // Expected: [1, 4]

        List<Interval<Integer>> intervals3 = Arrays.asList();
        System.out.println(mergeIntervals(intervals3)); // Expected: []

        List<Interval<Integer>> intervals4 = Arrays.asList(new Interval<>(1, 1));
        System.out.println(mergeIntervals(intervals4)); // Expected: [1, 1]

        List<Interval<Integer>> intervals5 = Arrays.asList(new Interval<>(1, 2), new Interval<>(3, 4), new Interval<>(5, 6));
        System.out.println(mergeIntervals(intervals5)); // Expected: [1, 2], [3, 4], [5, 6]
    }
}

class Interval<T extends Comparable<T>> {
    private T start;
    private T end;

    public Interval(T start, T end) {
        this.start = start;
        this.end = end;
    }

    public T getStart() {
        return start;
    }

    public T getEnd() {
        return end;
    }

    @Override
    public String toString() {
        return "[" + start + ", " + end + "]";
    }
}