import qrcode

url = "123456789"

img = qrcode.make(url)

img.save("booth_qr.png")

print("QR code saved as booth_qr.png")
