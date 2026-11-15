// A C++ class with a branching method. No standard-library headers, so the test does not depend
// on the host's C++ standard library installation.

class Jar {
    
    public:
    
    int nameCount = 5;
    
    const char *names[5]={"josh", "gabe", "sofia", "lucas", "ishaan"};
    
    const char *pull(int x) {
        const int y = x%5;
        if (y != 1) {   
            return names[y];
        }
        return "sorry gabe";
    }
    
};
    

int main()
{
    Jar j;
    j.pull(1);
    return 4;
    
}
