// Snippet 1 (Arvan et al., ASE 2026). Method body verbatim from study_materials/snippets_and_tasks.md.
import java.util.Set;

public class NamingUtilities {
    // Stubs so the snippet compiles; values from the study's output-prediction assumptions.
    static final int MAX_NAME_LENGTH = 10;
    static final Set<Character> VALID_NAME_SET = null;

    public static boolean isValidProjectName(String name) {
        if (name == null) {
            return false;
        }
        if (name.startsWith(".")) {
            return false;
        }
        if ((name.length() < 1) || (name.length() > MAX_NAME_LENGTH)) {
            return false;
        }
        for (int i = 0; i < name.length(); i++) {
            char c = name.charAt(i);
            if (!Character.isLetterOrDigit(c) && !VALID_NAME_SET.contains(c)) {
                return false;
            }
        }
        return true;
    }
}
