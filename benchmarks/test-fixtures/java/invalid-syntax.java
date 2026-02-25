public class BrokenSyntax {

    // Bug: missing semicolon on return statement (syntax error).
    public static int add(int a, int b) {
        return a + b
    }

    public static void main(String[] args) {
        System.out.println(add(1, 2));
    }
}
