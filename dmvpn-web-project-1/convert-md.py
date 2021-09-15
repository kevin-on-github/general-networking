import markdown2

with open('DMVPN-iBGP-Lab.md', 'r') as f:
    text = f.read()
    html = markdown2.markdown(text)

with open('post4-htmloutput.html', 'w') as f:
    f.write(html)