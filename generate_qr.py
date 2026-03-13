import qrcode

url = "234"

img = qrcode.make(url)

img.save("booth_qr.png")

print("QR code saved as booth_qr.png")
