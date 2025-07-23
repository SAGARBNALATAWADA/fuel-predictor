import qrcode

pdf_url = "https://drive.google.com/uc?export=download&id=1mVQNNfBxkli6TW6_lt8luqRQlGgXgzI4"
img = qrcode.make(pdf_url)
img.save('static/qr/generate_fuel_qr.png')

