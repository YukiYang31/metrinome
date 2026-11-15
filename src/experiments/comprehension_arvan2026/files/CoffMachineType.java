// Snippet 3 (Arvan et al., ASE 2026). Method body verbatim from study_materials/snippets_and_tasks.md.
import java.lang.reflect.Field;
import java.lang.reflect.Modifier;

public class CoffMachineType {
    // Stubs so the snippet compiles; values from the study's output-prediction assumptions.
    public static final short IMAGE_FILE_MACHINE_UNKNOWN = 0;
    public static final short IMAGE_FILE_MACHINE_AMD64 = (short) 34404;
    public static final short IMAGE_FILE_MACHINE_ARM = (short) 448;
    public static final short IMAGE_FILE_MACHINE_I386 = (short) 332;

    public static boolean isMachineTypeDefined(short type) {
        if (type == IMAGE_FILE_MACHINE_UNKNOWN) {
            // Unsupported machine type
            return false;
        }
        for (Field field : CoffMachineType.class.getDeclaredFields()) {
            if (!field.isSynthetic()) {
                int modifiers = field.getModifiers();
                if (Modifier.isFinal(modifiers) && Modifier.isStatic(modifiers)) {
                    try {
                        if (field.getShort(null) == type) {
                            return true;
                        }
                    } catch (IllegalAccessException e) {
                        continue;
                    }
                }
            }
        }
        return false;
    }
}
