import sys
import markdown2

try:
    with open(sys.argv[1], 'r') as f:
        text = f.read()
        html = markdown2.markdown(text)
except:
    print(f'{sys.argv[1]} file does not exist in current location')

try:
    with open(sys.argv[2], 'w') as f:
        f.write(html)
except:
    print(f'{sys.argv[2]} was unablew to be written. Check permissions and that the location exists.')