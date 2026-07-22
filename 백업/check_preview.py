import urllib.request

req = urllib.request.Request('http://127.0.0.1:5000/item-detail?itemCd=1297571')
try:
    with urllib.request.urlopen(req, timeout=15) as res:
        print('status', res.status)
        body = res.read(400).decode('utf-8', 'ignore')
        print(body)
except Exception as exc:
    print('ERROR', exc)
