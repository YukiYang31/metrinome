// Snippet 3 (Arvan et al., ASE 2026): manual C translation of CoffMachineType.isMachineTypeDefined (Ghidra).
// C has no reflection or exceptions:
//   - getDeclaredFields() -> opaque extern returning an array of field descriptors; for-each -> indexed for
//   - Modifier.isFinal/isStatic, field.isSynthetic -> opaque externs
//   - try { if (field.getShort(null) == type) return true; } catch (IllegalAccessException e) { continue; }
//     -> field_get_short returns nonzero on an access error, which takes the `continue` branch.
#include <stdbool.h>

#define IMAGE_FILE_MACHINE_UNKNOWN 0

typedef struct Field Field;
extern Field **get_declared_fields(int *count);
extern bool field_is_synthetic(const Field *field);
extern int field_get_modifiers(const Field *field);
extern bool modifier_is_final(int modifiers);
extern bool modifier_is_static(int modifiers);
extern int field_get_short(const Field *field, short *value);

bool isMachineTypeDefined(short type) {
    if (type == IMAGE_FILE_MACHINE_UNKNOWN) {
        return false;
    }
    int field_count;
    Field **fields = get_declared_fields(&field_count);
    for (int i = 0; i < field_count; i++) {
        Field *field = fields[i];
        if (!field_is_synthetic(field)) {
            int modifiers = field_get_modifiers(field);
            if (modifier_is_final(modifiers) && modifier_is_static(modifiers)) {
                short value;
                if (field_get_short(field, &value) != 0) {
                    continue;
                }
                if (value == type) {
                    return true;
                }
            }
        }
    }
    return false;
}
