import qrcode

url = ""

img = qrcode.make(url)

img.save("booth_qr.png")

print("QR code saved as booth_qr.png")
