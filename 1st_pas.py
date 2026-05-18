import re

normal_log = """
02021120149    PS CSTA=GGGXXXXXXXGGGXXXXXXXGGGXXXXXXXGGXXXXXXXXGGXXXXXXXXXXXXXXXXX
SLOT01=92,5900,장난감행운박스 SLOT02=79,5900,장난감행운박스 SLOT03=86,5900,장난감행운박스 SLOT11=80,5900,장난감행운박스 SLOT12=78,5900,장난감행운박스 SLOT13=89,5900,장난감행운박스
SLOT21=83,11000,랜덤피규어110 SLOT22=77,11000,랜덤피규어110 SLOT23=76,11000,랜덤피규어110 SLOT31=90,64000,왕실마차 SLOT32=95,64000,궁전베이커리 SLOT41=98,57000,어린이수영장 SLOT42=93,75000,사자우리

2022-05-31 오후 6:40:52    2022-05-31 오후 6:44:02    OK    CHOCO_VENDING/
"""

error_log="""
02021120149    PS CSTA=GGGXXXXXXXGGGXXXXXXXGGGXXXXXXXGGXXXXXXXXGGXXXXXXXXXXXXXXXXX
SLOT01=92,5900,장난감행운박스 //SLOT02=79,7900,장난감행운박스//SLOT03=86,5900,장난감행운박스 SLOT11=80,5900,장난감행운박스 SLOT12=78,5900,장난감행운박스 SLOT13=89,5900,장난감행운박스
SLOT21=83,11000,랜덤피규어110 SLOT22=77,11000,랜덤피규어110 SLOT23=76,11000,랜덤피규어110 SLOT31=90,64000,왕실마차 SLOT32=95,64000,궁전베이커리 SLOT41=98,57000,어린이수영장 SLOT42=93,75000,사자우리

2022-05-31 오후 6:15:52    2022-05-31 오후 6:18:02    OK    CHOCO_VENDING/
"""

def parse_log(log):
    parsed={
        "device_id":None,
        "status_code":None,
        "csta":None,
        "result":None,
        "device_type":None,
        "products":{},
        "warnings":[]
    }

# 비정사 구분자 검사(해당 로그는 쉼표와 빈칸으로 구분)
    if "//" in log:
        parsed["warnings"].append("비정상 구분자 '//' 발견")

# 헤더 정보 추출 / 장비ID, 상태코드, CSTA
    header_pattern=r"^\s*(\d+)\s+([A-Z]+)\s+CSTA=([GX]+)"
    header_match=re.search(header_pattern, log)

    if header_match:
        parsed["device_id"]=header_match.group(1)
        parsed["status_code"]=header_match.group(2)
        parsed["csta"]=header_match.group(3)

#결과값 추출 / OK, vending
    tail_pattern=r"\s(OK|FAIL|ERROR)\s+([A-Z_]+)/?"
    tail_match=re.search(tail_pattern, log)

    if tail_match:
        parsed["result"]=tail_match.group(1)
        parsed["device_type"]=tail_match.group(2)

# 상품슬롯 정보 추출
    products_pattern=r"(SLOT\d{2})=(\d+),(\d+),([^\s/]+)"

    for match in re.finditer(products_pattern, log, re.IGNORECASE):
        original_slot = match.group(1)
        slot=original_slot.upper()

        stock=int(match.group(2))
        price=int(match.group(3))
        name=match.group(4)
    # 소문자 감지 워닝
        if original_slot !=  slot:
            parsed["warnings"].append(
                f"슬롯 코드 대소문자 오류: {original_slot} ->{slot}"
            )
        parsed["products"][slot]={
            "stock":stock,
            "price":price,
            "name":name
        }
    return parsed

def compare_log(normal, target):
    anomal=[]

    normal_products = normal["products"]
    target_products = target["products"]
    
    # 정상로그에는 있으나 오류로그에 슬롯이 없을 때
    for slot in normal_products:
        if slot not in target_products:
            anomal.append(f"{slot} 누락")
    
    #정상로그에는 없으나 오류로그에 슬롯이 있을 때
    for slot in target_products:
        if slot not in normal_products:
            anomal.append(f"{slot}기준 외 슬롯")
    
    #슬롯 내 값 비교
    common_slots = normal_products.keys()&target_products.keys()

    for slot in common_slots:
        normal_item=normal_products[slot]
        target_item=target_products[slot]

        if normal_item["stock"] != target_item["stock"]:
            anomal.append(
                f"{slot} 재고 불일치: 정상{normal_item['stock']} / 오류{target_item['stock']}")

        if normal_item["price"] != target_item["price"]:
            anomal.append(
                f"{slot} 가격 불일치: 정상{normal_item['price']} / 오류{target_item['price']}")

        if normal_item["name"] != target_item["name"]:
            anomal.append(
                f"{slot}상 품명 불일치: 정상{normal_item['name']} / 오류{target_item['name']}")
    return anomal

normal_parsed = parse_log(normal_log)
error_parsed = parse_log(error_log)

anomal = compare_log(normal_parsed, error_parsed)

print("=== 정상 로그 파싱 ===")
print("장비ID: ", normal_parsed["device_id"])
print("상태코드: ", normal_parsed["status_code"])
print("처리결과: ", normal_parsed["result"])
print("장비타입: ", normal_parsed["device_type"])
print("상품 슬롯 수: ", len(normal_parsed["products"]))

print("=== 오류 로그 파싱 ===")
print("장비ID: ", error_parsed["device_id"])
print("상태코드: ", error_parsed["status_code"])
print("처리결과: ", error_parsed["result"])
print("장비타입: ", error_parsed["device_type"])
print("상품 슬롯 수: ", len(error_parsed["products"]))

print("=== 오류 로그 경고 ===")
if error_parsed["warnings"]:
    for warning in error_parsed["warnings"]:
        print("-",warning)
else:
    print("경고 없음")

print("=== 상세 비교 결과 ===")
if anomal:
    for anm in anomal:
        print("-", anm)
else:
    print("이상 없음")