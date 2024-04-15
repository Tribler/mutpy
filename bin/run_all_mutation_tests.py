#!/usr/bin/python3

import os
import re
import shutil
import sys

from bs4 import BeautifulSoup

if len(sys.argv) != 3:
    print(f"Usage: {__file__} [IPv8 folder] [Output folder]")
    sys.exit(1)

ipv8_path = os.path.abspath(sys.argv[1])
base_output_dir = os.path.abspath(os.path.join(sys.argv[2], 'mutation_tests'))
sys.path.insert(0, ipv8_path)
os.chdir(ipv8_path)

from run_all_tests import find_all_test_class_names

if __name__ != '__main__':
    print(__file__, "should be run stand-alone! Instead, it is being imported!", file=sys.stderr)
    sys.exit(1)

if os.path.isdir(base_output_dir):
    shutil.rmtree(base_output_dir)

test_paths = find_all_test_class_names()
test_files = set(['.'.join(path.split('.')[:-1]) for path in test_paths])
print("Found the following test files:")
print(test_files)

for test_path in test_files:
    print(">", test_path)
    class_under_test = test_path.replace('.test.', '.').replace('.test_', '.')
    if os.path.isfile(class_under_test.replace('.', '/') + ".py"):
        output_folder = os.path.abspath(os.path.join(base_output_dir, class_under_test))
        os.makedirs(output_folder, exist_ok=True)
        os.system(f"cd {ipv8_path} && mut.py --target {class_under_test} --unit-test {test_path} --report-html {output_folder}")
    else:
        print("Ignoring", class_under_test)

print("Done! Minimizing output")

output_paths = [os.path.join(base_output_dir, p) for p in os.listdir(base_output_dir)]

html_header = """
<!DOCTYPE html>
<html>
<head>
    <title>MutPy mutation report</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="bootstrap.min.css">
    <link rel="stylesheet" href="ipv8custom.css">

    <script src="jquery.js"></script>
    <script src="bootstrap.min.js"></script>
    <!--[if lt IE 9]>
    <script src="html5shiv.js"></script>
    <script src="respond.min.js"></script>
    <![endif]-->


</head>
<body>

<div class="container">
<table class="table">
"""

html_footer= """
</tr>
</table>
</div>

</body>
</html>
"""

html_body_elements = []

html_body_element = """
<tr><td>
<code>{}</code>
</td><td class="stdtdbarstyle">
{}
</td>
"""

for output_path in output_paths:
    index_file = os.path.join(output_path, 'index.html')
    if not os.path.exists(index_file):
        print(f"Skipping {index_file}, no index.html found!")
        continue
    test_name = ""
    progress_body = ""
    with open(index_file) as fp:
        soup = BeautifulSoup(fp, features="html.parser")
        for code_tag in soup.find_all("code", string=re.compile(".test.")):
            test_name = f"<a href='{os.path.relpath(index_file, base_output_dir)}'>{code_tag.string}</a>"
            break
        for progress_class in soup.find_all(class_ = "progress"):
            for child in list(progress_class.children):
                if hasattr(child, 'text'):
                    child.string = ' '
            progress_body = str(progress_class)
            break
    html_body_elements.append(html_body_element.format(test_name, progress_body))

with open(os.path.join(base_output_dir, 'index.html'), 'w') as html_output_handle:
    html_output_handle.write(html_header)
    for html_body_element in html_body_elements:
        html_output_handle.write(html_body_element)
    html_output_handle.write(html_footer)

shutil.copy(os.path.join('/root', 'MutPy', 'mutpy', 'templates', 'include', 'jquery.js'), base_output_dir)
shutil.copy(os.path.join('/root', 'MutPy', 'mutpy', 'templates', 'include', 'html5shiv.js'), base_output_dir)
shutil.copy(os.path.join('/root', 'MutPy', 'mutpy', 'templates', 'include', 'respond.min.js'), base_output_dir)
shutil.copy(os.path.join('/root', 'MutPy', 'mutpy', 'templates', 'include', 'bootstrap.min.css'), base_output_dir)
shutil.copy(os.path.join('/root', 'MutPy', 'mutpy', 'templates', 'include', 'bootstrap.min.js'), base_output_dir)
shutil.copy(os.path.join('/root', 'MutPy', 'mutpy', 'templates', 'include', 'glyphicons-halflings-regular.woff'), base_output_dir)
shutil.copy(os.path.join('/root', 'MutPy', 'mutpy', 'templates', 'include', 'ipv8custom.css'), base_output_dir)
