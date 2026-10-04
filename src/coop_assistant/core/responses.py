"""Approved response bank. Every number spoken comes from the decision facts, never from a model."""

import datetime as dt

SUPPORTED = ("en", "hi", "sw", "zh", "ko")

T = {
    "en": {
        "demo": "Just so you know, this is demo data. ",
        "ref": "According to {market}'s records from {date}, {form}{grade} in {district} is going for {ref} {cur} a kilo.",
        "lower": "So the {quote} you were offered is {diff} {cur} below that.",
        "higher": "So the {quote} you were offered is {diff} {cur} above that.",
        "equal": "So the offer you got matches that price.",
        "closing": "It's your call whether to sell, and do confirm the grade and moisture with your co-op.",
        "missing": "Please tell me the {fields}.",
        "unit": "Please give the price per kilogram.",
        "stale": "My latest record for {district} is from {date} and is out of date, so I cannot give a current price. Please check with your co-op.",
        "no_data": "I have no price data for {district}. Please check with your co-op.",
        "no_grade": "I have no price for grade {grade} here. Please check with your co-op.",
        "sparse": "The data for {district} is too thin (only {n} sample) to rely on. Please check with your co-op.",
        "unknown_district": "I only have demo data for Nyeri, Kiambu, Murang'a and Kirinyaga.",
        "currency": "I can only compare prices in Kenyan shillings.",
        "out_of_scope": "I can only help check coffee prices. For other questions I can connect you to a co-op officer.",
        "human_requested": "With your permission, a co-op officer will call you back.",
        "not_understood": "Sorry, I did not catch that. Please say it again.",
        "no_info": "Sorry, I don't have that information. I can ask an officer to call you back.",
        "fields": {"product_form": "coffee type (cherry or parchment)", "grade": "grade", "district": "district"},
        "forms": {"cherry": "coffee cherry", "parchment": "parchment coffee"},
        "grade_text": " grade {grade}",
        "sep": ", ",
        "currency_names": {"KES": "shillings"},
    },
    "hi": {
        "demo": "[डेमो डेटा] ",
        "ref": "{district} में {form}{grade} का संदर्भ भाव {ref} {cur} प्रति किलो है ({market}, {date} का, स्रोत: {source})।",
        "lower": "व्यापारी का {quote} का भाव इससे {diff} {cur} कम है।",
        "higher": "व्यापारी का {quote} का भाव इससे {diff} {cur} ज़्यादा है।",
        "equal": "व्यापारी का भाव इस संदर्भ भाव के बराबर है।",
        "closing": "यह सिर्फ़ जानकारी है, बेचने का फ़ैसला आपका है। ग्रेड और नमी की पुष्टि अपनी सहकारी समिति से करें।",
        "missing": "कृपया बताइए: {fields}।",
        "unit": "कृपया भाव प्रति किलो बताइए।",
        "stale": "{district} का मेरे पास आख़िरी रिकॉर्ड {date} का है और पुराना हो चुका है, इसलिए मैं अभी का भाव नहीं बता सकता। कृपया सहकारी समिति से पूछें।",
        "no_data": "{district} के लिए मेरे पास कोई भाव नहीं है। कृपया सहकारी समिति से पूछें।",
        "no_grade": "ग्रेड {grade} के लिए मेरे पास भाव नहीं है। कृपया सहकारी समिति से पूछें।",
        "sparse": "{district} का डेटा बहुत कम है (सिर्फ़ {n} नमूना), इस पर भरोसा नहीं किया जा सकता। कृपया सहकारी समिति से पूछें।",
        "unknown_district": "मेरे पास सिर्फ़ न्येरी, किआम्बु, मुरांगा और किरिन्यागा का डेमो डेटा है।",
        "currency": "मैं सिर्फ़ केन्याई शिलिंग में भाव की तुलना कर सकता हूँ।",
        "out_of_scope": "मैं सिर्फ़ कॉफ़ी का भाव जाँचने में मदद कर सकता हूँ। दूसरे सवालों के लिए मैं आपको सहकारी अधिकारी से जोड़ सकता हूँ।",
        "human_requested": "आपकी अनुमति से, सहकारी अधिकारी आपको वापस कॉल करेंगे।",
        "not_understood": "माफ़ कीजिए, मैं समझ नहीं पाया। कृपया दोबारा बोलिए।",
        "no_info": "माफ़ कीजिए, मेरे पास यह जानकारी नहीं है। मैं किसी अधिकारी से आपको वापस कॉल करवा सकता हूँ।",
        "fields": {"product_form": "कॉफ़ी का प्रकार (चेरी या पार्चमेंट)", "grade": "ग्रेड", "district": "ज़िला"},
        "forms": {"cherry": "कॉफ़ी चेरी", "parchment": "पार्चमेंट कॉफ़ी"},
        "grade_text": " ग्रेड {grade}",
        "sep": ", ",
    },
    "sw": {
        "demo": "[DATA YA MAJARIBIO] ",
        "ref": "Bei ya marejeleo ya {form}{grade} huko {district} ni {cur} {ref} kwa kilo ({market}, tarehe {date}, chanzo: {source}).",
        "lower": "Bei ya mnunuzi ya {quote} iko chini kwa {cur} {diff} kuliko bei hii.",
        "higher": "Bei ya mnunuzi ya {quote} iko juu kwa {cur} {diff} kuliko bei hii.",
        "equal": "Bei ya mnunuzi ni sawa na bei hii ya marejeleo.",
        "closing": "Hii ni taarifa tu; uamuzi wa kuuza ni wako. Thibitisha daraja na unyevu na chama chako cha ushirika.",
        "missing": "Tafadhali niambie: {fields}.",
        "unit": "Tafadhali taja bei kwa kilo moja.",
        "stale": "Rekodi yangu ya mwisho ya {district} ni ya tarehe {date} na imepitwa na wakati, kwa hiyo siwezi kutoa bei ya sasa. Tafadhali uliza chama chako cha ushirika.",
        "no_data": "Sina data ya bei ya {district}. Tafadhali uliza chama chako cha ushirika.",
        "no_grade": "Sina bei ya daraja {grade} hapa. Tafadhali uliza chama chako cha ushirika.",
        "sparse": "Data ya {district} ni chache mno (sampuli {n} tu) kuweza kuitegemea. Tafadhali uliza chama chako cha ushirika.",
        "unknown_district": "Nina data ya majaribio ya Nyeri, Kiambu, Murang'a na Kirinyaga pekee.",
        "currency": "Ninaweza kulinganisha bei kwa shilingi za Kenya pekee.",
        "out_of_scope": "Ninaweza kusaidia kuangalia bei ya kahawa pekee. Kwa maswali mengine, naweza kukuunganisha na afisa wa ushirika.",
        "human_requested": "Kwa idhini yako, afisa wa ushirika atakupigia simu.",
        "not_understood": "Samahani, sikuelewa. Tafadhali rudia.",
        "no_info": "Samahani, sina taarifa hiyo. Naweza kumwomba afisa akupigie simu.",
        "fields": {"product_form": "aina ya kahawa (matunda au parchment)", "grade": "daraja", "district": "kaunti"},
        "forms": {"cherry": "matunda ya kahawa", "parchment": "kahawa ya parchment"},
        "grade_text": " daraja {grade}",
        "sep": ", ",
    },
    "zh": {
        "demo": "【演示数据】",
        "ref": "{district}{form}{grade}的参考价格为每公斤 {ref} {cur}（{market}，{date} 观测，来源：{source}）。",
        "lower": "买家出价 {quote}，比参考价低 {diff} {cur}。",
        "higher": "买家出价 {quote}，比参考价高 {diff} {cur}。",
        "equal": "买家出价与参考价相同。",
        "closing": "以上仅供参考，是否出售由您决定。请向合作社确认等级和含水量。",
        "missing": "请告诉我：{fields}。",
        "unit": "请按每公斤报价。",
        "stale": "我掌握的{district}最新记录是 {date} 的，已经过期，无法提供当前价格。请咨询您的合作社。",
        "no_data": "我没有{district}的价格数据。请咨询您的合作社。",
        "no_grade": "我没有 {grade} 级的价格。请咨询您的合作社。",
        "sparse": "{district}的数据太少（仅 {n} 个样本），不可靠。请咨询您的合作社。",
        "unknown_district": "我只有 Nyeri、Kiambu、Murang'a 和 Kirinyaga 的演示数据。",
        "currency": "我只能比较以肯尼亚先令计价的价格。",
        "out_of_scope": "我只能帮助查询咖啡价格。其他问题我可以为您转接合作社工作人员。",
        "human_requested": "经您同意，合作社工作人员会给您回电。",
        "not_understood": "抱歉，我没听清，请再说一遍。",
        "no_info": "抱歉，我没有这方面的信息。我可以请工作人员给您回电。",
        "fields": {"product_form": "咖啡类型（鲜果或羊皮纸豆）", "grade": "等级", "district": "地区"},
        "forms": {"cherry": "咖啡鲜果", "parchment": "羊皮纸咖啡豆"},
        "grade_text": "（{grade}级）",
        "sep": "、",
    },
    "ko": {
        "demo": "[시연 데이터] ",
        "ref": "{district} {form}{grade}의 참고 가격은 kg당 {ref} {cur}입니다 ({market}, {date} 관측, 출처: {source}).",
        "lower": "구매자 제시가 {quote}는 참고 가격보다 {diff} {cur} 낮습니다.",
        "higher": "구매자 제시가 {quote}는 참고 가격보다 {diff} {cur} 높습니다.",
        "equal": "구매자 제시가는 참고 가격과 같습니다.",
        "closing": "이 정보는 참고용이며, 판매 결정은 본인이 하십시오. 등급과 수분은 협동조합에 확인하세요.",
        "missing": "다음을 알려 주세요: {fields}.",
        "unit": "kg당 가격으로 말씀해 주세요.",
        "stale": "{district}의 최신 기록은 {date} 기준으로 오래되어 현재 가격을 알려 드릴 수 없습니다. 협동조합에 문의하세요.",
        "no_data": "{district}의 가격 데이터가 없습니다. 협동조합에 문의하세요.",
        "no_grade": "{grade} 등급의 가격이 없습니다. 협동조합에 문의하세요.",
        "sparse": "{district}의 데이터가 너무 적어(표본 {n}개) 신뢰할 수 없습니다. 협동조합에 문의하세요.",
        "unknown_district": "Nyeri, Kiambu, Murang'a, Kirinyaga의 시연 데이터만 있습니다.",
        "currency": "케냐 실링 가격만 비교할 수 있습니다.",
        "out_of_scope": "커피 가격 확인만 도와드릴 수 있습니다. 다른 질문은 협동조합 담당자와 연결해 드릴 수 있습니다.",
        "human_requested": "동의하시면 협동조합 담당자가 다시 전화드립니다.",
        "not_understood": "죄송합니다, 잘 듣지 못했습니다. 다시 말씀해 주세요.",
        "no_info": "죄송합니다, 그 정보는 없습니다. 담당자가 다시 전화드리도록 할 수 있습니다.",
        "fields": {"product_form": "커피 종류(체리 또는 파치먼트)", "grade": "등급", "district": "지역"},
        "forms": {"cherry": "커피 체리", "parchment": "파치먼트 커피"},
        "grade_text": " {grade}등급",
        "sep": ", ",
    },
}


def _num(value):
    return f"{value:,.0f}" if float(value).is_integer() else f"{value:,.2f}"


def render(decision, lang):
    t = T[lang if lang in SUPPORTED else "en"]
    f = decision.get("facts", {})
    reason = decision.get("reason")
    grade = f.get("grade")
    grade_text = t["grade_text"].format(grade=grade) if grade and grade != "ungraded" else ""

    if decision["state"] == "ANSWER":
        cur = t.get("currency_names", {}).get(f["currency"], f["currency"])
        date = f["observed_at"]
        if lang == "en":
            d = dt.date.fromisoformat(date)
            date = f"{d:%B} {d.day}"
        parts = [t["demo"] + t["ref"].format(
            form=t["forms"][f["product_form"]], grade=grade_text, district=f["district"],
            ref=_num(f["reference"]), cur=cur, market=f["market"], date=date, source=f["source"],
        )]
        if "quote" in f:
            diff = f["difference"]
            key = "equal" if diff == 0 else ("lower" if diff < 0 else "higher")
            parts.append(t[key].format(quote=_num(f["quote"]), diff=_num(abs(diff)), cur=cur))
        parts.append(t["closing"])
        return " ".join(parts)

    if reason == "missing":
        return t["missing"].format(fields=t["sep"].join(t["fields"][m] for m in f["missing"]))
    if reason == "stale":
        return t["demo"] + t["stale"].format(district=f["district"], date=f["observed_at"])
    if reason == "sparse":
        return t["demo"] + t["sparse"].format(district=f["district"], n=f["sample_count"])
    if reason == "no_data":
        return t["no_data"].format(district=f["district"])
    if reason == "no_grade":
        return t["no_grade"].format(grade=f["grade"])
    return t[reason]
