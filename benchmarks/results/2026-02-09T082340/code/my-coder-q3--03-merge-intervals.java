import org.junit.jupiter.api.Test;
import java.util.*;
import static org.junit.jupiter.api.Assertions.*;

public class IntervalMergerTest {
    @Test
    public void testMergeIntervals() {
        // Test case 1: No overlaps
        List<Interval<Integer>> intervals1 = Arrays.asList(
                new Interval<>(1, 2),
                new Interval<>(3, 4)
        );
        List<Interval<Integer>> expected1 = Arrays.asList(
                new Interval<>(1, 2),
                new Interval<>(3, 4)
        );
        assertEquals(expected1, IntervalMerger.mergeIntervals(intervals1));

        // Test case 2: All overlapping
        List<Interval<Integer>> intervals2 = Arrays.asList(
                new Interval<>(1, 5),
                new Interval<>(2, 3),
                new Interval<>(4, 7)
        );
        List<Interval<Integer>> expected2 = Arrays.asList(
                new Interval<>(1, 7)
        );
        assertEquals(expected2, IntervalMerger.mergeIntervals(intervals2));

        // Test case 3: Partial overlaps
        List<Interval<Integer>> intervals3 = Arrays.asList(
                new Interval<>(1, 3),
                new Interval<>(2, 4),
                new Interval<>(5, 7)
        );
        List<Interval<Integer>> expected3 = Arrays.asList(
                new Interval<>(1, 4),
                new Interval<>(5, 7)
        );
        assertEquals(expected3, IntervalMerger.mergeIntervals(intervals3));

        // Test case 4: Contained intervals
        List<Interval<Integer>> intervals4 = Arrays.asList(
                new Interval<>(1, 5),
                new Interval<>(2, 3),
                new Interval<>(4, 6)
        );
        List<Interval<Integer>> expected4 = Arrays.asList(
                new Interval<>(1, 6)
        );
        assertEquals(expected4, IntervalMerger.mergeIntervals(intervals4));

        // Test case 5: Single interval
        List<Interval<Integer>> intervals5 = Arrays.asList(
                new Interval<>(1, 10)
        );
        List<Interval<Integer>> expected5 = Arrays.asList(
                new Interval<>(1, 10)
        );
        assertEquals(expected5, IntervalMerger.mergeIntervals(intervals5));

        // Test case 6: Empty input
        List<Interval<Integer>> intervals6 = new ArrayList<>();
        List<Interval<Integer>> expected6 = new ArrayList<>();
        assertEquals(expected6, IntervalMerger.mergeIntervals(intervals6));

        // Test case 7: Unsorted input
        List<Interval<Integer>> intervals7 = Arrays.asList(
                new Interval<>(3, 5),
                new Interval<>(1, 4)
        );
        List<Interval<Integer>> expected7 = Arrays.asList(
                new Interval<>(1, 5)
        );
        assertEquals(expected7, IntervalMerger.mergeIntervals(intervals7));
    }
}