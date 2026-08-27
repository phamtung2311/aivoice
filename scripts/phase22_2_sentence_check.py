s = "Mọi người đang ở đây."
print("repr:", repr(s))
print("codepoints:", [f"U+{ord(c):04X}" for c in s])
print("utf8", s.encode("utf-8").hex())
print("nfc_identical:", s == __import__("unicodedata").normalize("NFC", s))