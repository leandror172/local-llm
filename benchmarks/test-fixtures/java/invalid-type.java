public class TypeMismatch {

    // Bug: passing String where int is expected (type error).
    public static int square(int n) {
        return n * n;
    }

    public static void main(String[] args) {
        int result = square("hello");
        System.out.println(result);
    }
}
