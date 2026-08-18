import java.util.*;

public class IntervalMergerTest {
    public static void main(String[] args) {
        // Test case 1: No overlaps
        List<Interval<Integer>> test1 = Arrays.asList(
            new Interval<>(1, 2),
            new Interval<>(3, 4)
        );
        System.out.println("Test 1: " + IntervalMerger.mergeIntervals(test1));

        // Test case 2: All overlapping
        List<Interval<Integer>> test2 = Arrays.asList(
            new Interval<>(1, 5),
            new Interval<>(2, 8),
            new Interval<>(3, 10)
        );
        System.out.println("Test 2: " + IntervalMerger.mergeIntervals(test2));

        // Test case 3: Partial overlaps
        List<Interval<Integer>> test3 = Arrays.asList(
            new Interval<>(1, 3),
            new Interval<>(2, 4),
            new Interval<>(5, 7)
        );
        System.out.println("Test 3: " + IntervalMerger.mergeIntervals(test3));

        // Test case 4: Contained intervals
        List<Interval<Integer>> test4 = Arrays.asList(
            new Interval<>(1, 5),
            new Interval<>(2, 3)
        );
        System.out.println("Test 4: " + IntervalMerger.mergeIntervals(test4));

        // Test case 5: Single element
        List<Interval<Integer>> test5 = Arrays.asList(
            new Interval<>(1, 2)
        );
        System.out.println("Test 5: " + IntervalMerger.mergeIntervals(test5));

        // Test case 6: Empty input
        List<Interval<Integer>> test6 = new ArrayList<>();
        System.out.println("Test 6: " + IntervalMerger.mergeIntervals(test6));

        // Test case 7: Unsorted input
        List<Interval<Integer>> test7 = Arrays.asList(
            new Interval<>(3, 5),
            new Interval<>(1, 4)
        );
        System.out.println("Test 7: " + IntervalMerger.mergeIntervals(test7));
    }
}