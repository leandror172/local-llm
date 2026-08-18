import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.List;

public class IntervalMerger {

    public static List<Interval> mergeIntervals(List<Interval> intervals) {
        if (intervals == null || intervals.isEmpty()) {
            return Collections.emptyList();
        }

        // Sort intervals by start value
        Collections.sort(intervals, Comparator.comparing(Interval::getStart));

        List<Interval> merged = new ArrayList<>();
        Interval current = intervals.get(0);

        for (Interval interval : intervals) {
            if (interval.getStart() <= current.getEnd()) {
                // Overlapping intervals, merge them
                current.setEnd(Math.max(current.getEnd(), interval.getEnd()));
            } else {
                // Non-overlapping interval, add to result and update current
                merged.add(current);
                current = interval;
            }
        }

        // Add the last interval
        merged.add(current);

        return merged;
    }

    public static void main(String[] args) {
        List<Interval> intervals = new ArrayList<>();
        intervals.add(new Interval(1, 3));
        intervals.add(new Interval(2, 6));
        intervals.add(new Interval(8, 10));
        intervals.add(new Interval(15, 18));

        List<Interval> mergedIntervals = mergeIntervals(intervals);
        for (Interval interval : mergedIntervals) {
            System.out.println(interval.getStart() + " -> " + interval.getEnd());
        }
    }

    static class Interval implements Comparable<Interval> {
        private int start;
        private int end;

        public Interval(int start, int end) {
            this.start = start;
            this.end = end;
        }

        public int getStart() {
            return start;
        }

        public void setStart(int start) {
            this.start = start;
        }

        public int getEnd() {
            return end;
        }

        public void setEnd(int end) {
            this.end = end;
        }

        @Override
        public int compareTo(Interval other) {
            return Integer.compare(this.start, other.start);
        }
    }
}