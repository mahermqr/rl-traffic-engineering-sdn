import sys, os, subprocess, shutil

# Ensure path is included
sys.path.insert(0, '/home/maher/Downloads/EC499t/report_builder')

from p01_preamble import PREAMBLE_AND_FRONTMATTER
from p02_ch1_intro import CHAPTER_1_INTRO
from p03_ch2_background import CHAPTER_2_BACKGROUND
from p04_ch3_related import CHAPTER_3_RELATED
from p05_ch4_design_exp import CHAPTER_4_DESIGN_EXP
from p06_ch4_eval_results import CHAPTER_4_EVAL_RESULTS
from p07_ch5_conclusion import CHAPTER_5_CONCLUSION
from p08_ch6_future_work import CHAPTER_6_FUTURE_WORK
from p09_references_appendices import REFERENCES_AND_APPENDICES

full_tex = (
    PREAMBLE_AND_FRONTMATTER + "\n" +
    CHAPTER_1_INTRO + "\n" +
    CHAPTER_2_BACKGROUND + "\n" +
    CHAPTER_3_RELATED + "\n" +
    CHAPTER_4_DESIGN_EXP + "\n" +
    CHAPTER_4_EVAL_RESULTS + "\n" +
    CHAPTER_5_CONCLUSION + "\n" +
    CHAPTER_6_FUTURE_WORK + "\n" +
    REFERENCES_AND_APPENDICES
)

targets = [
    '/home/maher/Downloads/EC499t/GRADUATION_PROJECT_REPORT.tex',
    '/home/maher/Downloads/EC499t/Project_Report_EC499_Final.tex',
    '/home/maher/Downloads/EC499t/main.tex',
    '/home/maher/Downloads/EC499t/Reinforcement_Learning_for_Adaptive_Traffic_Engineering_in_an_SDN_Network/EC499report/docs/Project_Report_EC499_Monolithic.tex'
]

for t in targets:
    print(f"Writing master report to: {t}")
    with open(t, 'w') as f:
        f.write(full_tex)

print(f"Total characters: {len(full_tex)}, Total lines: {len(full_tex.splitlines())}")

# Compile using tectonic
print("Compiling Project_Report_EC499_Final.tex with tectonic...")
res = subprocess.run(
    ['/home/maher/.local/bin/tectonic', '/home/maher/Downloads/EC499t/Project_Report_EC499_Final.tex'],
    cwd='/home/maher/Downloads/EC499t',
    capture_output=True,
    text=True
)

if res.returncode == 0:
    print("SUCCESS: Tectonic compiled Project_Report_EC499_Final.pdf cleanly!")
    pdf_src = '/home/maher/Downloads/EC499t/Project_Report_EC499_Final.pdf'
    shutil.copyfile(pdf_src, '/home/maher/Downloads/EC499t/GRADUATION_PROJECT_REPORT.pdf')
    shutil.copyfile(pdf_src, '/home/maher/Downloads/EC499t/Reinforcement_Learning_for_Adaptive_Traffic_Engineering_in_an_SDN_Network/EC499report/docs/Project_Report_EC499_Final.pdf')
    print("Copied PDF to GRADUATION_PROJECT_REPORT.pdf and EC499report/docs/Project_Report_EC499_Final.pdf")
else:
    print("COMPILE ERROR:")
    print("STDOUT:", res.stdout[-1500:])
    print("STDERR:", res.stderr[-1500:])
    sys.exit(1)
