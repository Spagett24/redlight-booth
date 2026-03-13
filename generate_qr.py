import qrcode

url = "http://192.168.1.245:8000"

img = qrcode.make(url)

img.save("booth_qr.png")

print("QR code saved as booth_qr.png")
