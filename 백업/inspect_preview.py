import urllib.request

url = 'http://127.0.0.1:5000/item-detail?itemCd=1297571'
with urllib.request.urlopen(url, timeout=15) as res:
    html = res.read().decode('utf-8', 'ignore')
    print('has iframe? ', '<iframe' in html.lower())
    print('has metaInfoTbl? ', 'metaInfoTbl' in html)
    print(html[:800])
