import sys
import fitz
sys.stdout.reconfigure(encoding='utf-8')
doc = fitz.open(r"c:\Work\LLNL\LLNL-26\Project\papers\ICL\llms-are-invertible.pdf")
text = ""
for page in doc:
    text += page.get_text()
# Write to file instead
with open("paper_text.txt", "w", encoding="utf-8") as f:
    f.write(text)
print("Done. Written to paper_text.txt")
