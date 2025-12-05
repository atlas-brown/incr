import textwrap, sys

N_FILES = 5
FUNS_PER_FILE = 2000   # crank these up to taste
LOOP_ITERS    = 10000

for i in range(N_FILES):
    name = f"file{i:03d}.c"
    with open(name, "w") as f:
        f.write("#include <math.h>\n\n")
        for j in range(FUNS_PER_FILE):
            f.write(textwrap.dedent(f"""
            double func_{i}_{j}(double x) {{
                #pragma GCC optimize ("O3,unroll-loops")
                for (int k = 0; k < {LOOP_ITERS}; ++k) {{
                    x = sin(x) * cos(x) + sqrt(fabs(x)) + k * 1e-6;
                }}
                return x;
            }}
            """))
        f.write("\n// prevent dead-code elimination\n")
        f.write("double use_all(double x) {\n")
        for j in range(FUNS_PER_FILE):
            f.write(f"  x += func_{i}_{j}(x);\n")
        f.write("  return x;\n}\n")
