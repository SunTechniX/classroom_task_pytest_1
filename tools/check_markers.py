# tools/check_markers.py
import sys

with open("tests/test_calculator.py", encoding="utf-8") as f1, \
     open("tests/test_string_utils.py", encoding="utf-8") as f2:
    content = f1.read() + f2.read()

math_ok = "@pytest.mark.math" in content
string_ok = "@pytest.mark.string" in content

if math_ok and string_ok:
    print("OK: markers found")
    sys.exit(0)
else:
    print("ERROR: missing markers")
    sys.exit(1)
