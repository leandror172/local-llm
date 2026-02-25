public class UndefinedRef {

    // Bug: calling a method that does not exist in JDK or this class.
    public static void main(String[] args) {
        String result = nonExistentHelper("input");
        System.out.println(result);
    }
}
