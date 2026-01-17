import easyocr
reader = easyocr.Reader(['en'])
result = reader.readtext('Screenshot 2026-01-16 022813.png',detail=0,paragraph=True)
medicine="".join(result)
print(medicine)